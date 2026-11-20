import asyncio
import html
import logging
from decimal import Decimal

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from django.db import transaction
from django.utils import timezone

from bot.config import ADMIN_IDS
from bot.database import AuthToken, BotAdmin, ServiceOrder, sync_to_async
from bot.handlers.crm import build_order_action_kb
from bot.states.client_states import CourierLocationStates, LoginAuthStates
from core.distance import (
    build_google_maps_url,
    build_yandex_maps_url,
    calculate_courier_fee_uzs,
    calculate_road_distance_km,
)
from core.telegram_auth import (
    is_uzbek_phone_number,
    normalize_phone_number,
    normalize_uzbek_phone_number,
    upsert_telegram_user,
)

logger = logging.getLogger("mobiprice_bot.client")

router = Router(name="client")


def _validate_login_token(token_value: str, telegram_id: int | None = None) -> str:
    """Deep-Link login tokenining joriy holatini va egasini (agar belgilangan bo'lsa) tekshirish"""
    if not token_value:
        return "invalid"

    auth_token = AuthToken.objects.filter(token=token_value).first()
    if not auth_token:
        return "invalid"
    if auth_token.rejected_reason:
        return "rejected"
    if auth_token.is_used or auth_token.is_confirmed:
        return "used"
    if auth_token.expires_at <= timezone.now():
        return "expired"
    if (
        auth_token.expected_telegram_id
        and telegram_id is not None
        and int(auth_token.expected_telegram_id) != int(telegram_id)
    ):
        return "wrong_account"
    return "ok"


def _reject_login_token(token_value: str, reason: str) -> None:
    """Tokenni rad etilgan deb belgilash (masalan: O'zbekiston +998 raqami emas)"""
    if not token_value:
        return
    AuthToken.objects.filter(
        token=token_value,
        is_used=False,
        is_confirmed=False,
    ).update(rejected_reason=str(reason)[:64], is_used=True)


def _confirm_login_token(token_value: str, user_data: dict) -> tuple[bool, str]:
    """Deep-Link login tokenini tasdiqlangan O'zbekiston (+998) telefon raqami bilan bog'lab tasdiqlash"""
    if not token_value:
        return False, "invalid"

    raw_phone = (user_data or {}).get('phone_number', '')
    normalized_any = normalize_phone_number(raw_phone)
    if not normalized_any:
        return False, "phone_required"

    verified_uz_phone = normalize_uzbek_phone_number(raw_phone)
    if not verified_uz_phone:
        _reject_login_token(token_value, "non_uz_phone")
        return False, "non_uz_phone"

    clean_user_data = dict(user_data)
    clean_user_data['phone_number'] = verified_uz_phone
    tg_id = int(clean_user_data['id'])

    now = timezone.now()
    with transaction.atomic():
        auth_token = AuthToken.objects.select_for_update().filter(token=token_value).first()
        if not auth_token:
            return False, "invalid"
        if auth_token.rejected_reason:
            return False, "rejected"
        if auth_token.is_used or auth_token.is_confirmed:
            return False, "used"
        if auth_token.expires_at <= now:
            return False, "expired"
        if auth_token.expected_telegram_id and int(auth_token.expected_telegram_id) != tg_id:
            return False, "wrong_account"

        tg_user = upsert_telegram_user(clean_user_data)
        auth_token.telegram_user = tg_user
        auth_token.is_confirmed = True
        auth_token.save(update_fields=['telegram_user', 'is_confirmed'])
        return True, "confirmed"


def validate_verified_own_contact(message: Message) -> tuple[bool, str, str]:
    """
    ReplyKeyboard request_contact=True tugmasi orqali yuborilgan 100% haqiqiy o'z
    O'zbekiston (+998) Telegram raqamini qat'iy tekshirish:
    - Faqat shaxsiy chat (private)
    - Forward qilingan yoki inline bot orqali yuborilgan bo'lmasligi
    - contact.user_id == message.from_user.id (boshqa odam kontakti va ro'yxatdan o'tmagan kontakt rad etiladi)
    - contact.vcard bo'sh bo'lishi (kontaktlar kitobidan ulashilgan vCard rad etiladi)
    - Telefon raqami faqat O'zbekiston (+998XXXXXXXXX) raqami bo'lishi shart
    """
    chat = getattr(message, 'chat', None)
    if not chat or getattr(chat, 'type', None) != 'private':
        return False, "not_private", ""

    from_user = getattr(message, 'from_user', None)
    contact = getattr(message, 'contact', None)
    if not from_user or not contact:
        return False, "no_contact", ""

    if any([
        getattr(message, 'forward_origin', None),
        getattr(message, 'forward_date', None),
        getattr(message, 'forward_from', None),
        getattr(message, 'forward_from_chat', None),
        getattr(message, 'forward_sender_name', None),
        getattr(message, 'is_automatic_forward', None),
    ]):
        return False, "forwarded", ""

    if getattr(message, 'via_bot', None):
        return False, "via_bot", ""

    contact_uid = getattr(contact, 'user_id', None)
    if contact_uid is None or int(contact_uid) != int(from_user.id):
        return False, "not_own_contact", ""

    if str(getattr(contact, 'vcard', '') or '').strip():
        return False, "vcard_contact", ""

    normalized_phone = normalize_phone_number(getattr(contact, 'phone_number', '') or '')
    if not normalized_phone:
        return False, "invalid_phone", ""

    if not is_uzbek_phone_number(normalized_phone):
        return False, "non_uz_phone", normalized_phone

    return True, "ok", normalized_phone


def _validate_courier_token(token_value: str, telegram_id: int) -> tuple[str, dict]:
    """Kuryer deep-link tokenini tekshirish va buyurtma qisqa ma'lumotlarini qaytarish"""
    if not token_value:
        return "invalid", {}

    order = (
        ServiceOrder.objects
        .select_related('telegram_user', 'phone', 'comparison', 'comparison__issue')
        .filter(courier_token=token_value)
        .first()
    )
    if not order:
        return "invalid", {}
    if order.status != 'pending_location':
        return "already_processed", {}
    if order.courier_token_expires_at and order.courier_token_expires_at <= timezone.now():
        return "expired", {}
    if not order.telegram_user or order.telegram_user.telegram_id != telegram_id:
        return "forbidden", {}

    phone_str = order.phone.name if order.phone else "Smartfon"
    if order.comparison:
        issue_title = order.comparison.issue.title if getattr(order.comparison, 'issue', None) else ""
        part_str = f"{issue_title} ({order.comparison.title})" if issue_title else order.comparison.title
        part_price_uzs = int(order.comparison.total_price_uzs)
    else:
        part_str = "Umumiy konsultatsiya"
        part_price_uzs = 0

    return "ok", {
        'order_pk': order.id,
        'order_id': order.order_id,
        'phone_str': phone_str,
        'part_str': part_str,
        'part_price_uzs': part_price_uzs,
    }


def _check_pending_courier_order(order_pk: int, token_value: str, telegram_id: int) -> str:
    """Lokatsiya hisoblashdan avval buyurtma hali ham yaroqli ekanligini tekshirish"""
    order = (
        ServiceOrder.objects
        .select_related('telegram_user')
        .filter(pk=order_pk)
        .first()
    )
    if not order:
        return "invalid"
    if order.status != 'pending_location':
        return "already_processed"
    if token_value and order.courier_token != token_value:
        return "invalid"
    if order.courier_token_expires_at and order.courier_token_expires_at <= timezone.now():
        return "expired"
    if not order.telegram_user or order.telegram_user.telegram_id != telegram_id:
        return "forbidden"
    return "ok"


def _finalize_courier_order(
    order_pk: int,
    token_value: str,
    telegram_id: int,
    lat: float,
    lon: float,
    distance_km: float,
    delivery_fee_uzs: int,
) -> tuple[str, dict]:
    """Lokatsiya, masofa va kuryer narxini atomar tarzda saqlab, menejer ID larini qaytarish"""
    now = timezone.now()
    with transaction.atomic():
        order = (
            ServiceOrder.objects
            .select_for_update()
            .select_related('telegram_user', 'phone', 'comparison', 'comparison__issue')
            .filter(pk=order_pk)
            .first()
        )
        if not order:
            return "invalid", {}
        if order.status != 'pending_location':
            return "already_processed", {}
        if token_value and order.courier_token != token_value:
            return "invalid", {}
        if order.courier_token_expires_at and order.courier_token_expires_at <= now:
            return "expired", {}
        if not order.telegram_user or order.telegram_user.telegram_id != telegram_id:
            return "forbidden", {}

        part_price_total = int(order.comparison.total_price_uzs) if order.comparison else 0
        final_total = part_price_total + int(delivery_fee_uzs)

        order.latitude = float(lat)
        order.longitude = float(lon)
        order.distance_km = Decimal(f"{float(distance_km):.2f}")
        order.delivery_fee_uzs = Decimal(int(delivery_fee_uzs))
        order.final_total_uzs = Decimal(int(final_total))
        order.status = 'new'
        order.courier_token = None
        order.courier_token_expires_at = None
        update_fields = [
            'latitude',
            'longitude',
            'distance_km',
            'delivery_fee_uzs',
            'final_total_uzs',
            'status',
            'courier_token',
            'courier_token_expires_at',
        ]
        tg_user = order.telegram_user
        effective_phone = order.phone_number or (tg_user.phone_number if tg_user else '')
        if effective_phone and order.phone_number != effective_phone:
            order.phone_number = effective_phone[:30]
            update_fields.append('phone_number')

        order.save(update_fields=update_fields)

        phone_str = order.phone.name if order.phone else "Ko'rsatilmagan"
        if order.comparison:
            issue_title = order.comparison.issue.title if getattr(order.comparison, 'issue', None) else ""
            part_str = f"{issue_title} ({order.comparison.title})" if issue_title else order.comparison.title
        else:
            part_str = "Umumiy konsultatsiya"

        # Menejerlar va bosh adminlar ID lari
        manager_ids = []
        for aid in ADMIN_IDS:
            if aid not in manager_ids:
                manager_ids.append(aid)

        db_manager_ids = list(
            BotAdmin.objects.filter(
                is_active=True,
                role__in=['manager', 'both'],
            ).exclude(telegram_id__isnull=True).values_list('telegram_id', flat=True)
        )
        for aid in db_manager_ids:
            try:
                aid_int = int(aid)
                if aid_int not in manager_ids:
                    manager_ids.append(aid_int)
            except (TypeError, ValueError):
                continue

        return "ok", {
            'order_pk': order.id,
            'order_id': order.order_id,
            'client_name': order.client_name,
            'phone_number': order.phone_number or '',
            'tg_username': tg_user.username if tg_user else '',
            'tg_id': tg_user.telegram_id if tg_user else telegram_id,
            'tg_profile_url': tg_user.tg_profile_url if tg_user else f"tg://user?id={telegram_id}",
            'phone_str': phone_str,
            'part_str': part_str,
            'has_comparison': bool(order.comparison_id),
            'part_price_uzs': part_price_total,
            'distance_km': float(order.distance_km),
            'delivery_fee_uzs': int(delivery_fee_uzs),
            'final_total_uzs': int(final_total),
            'latitude': float(lat),
            'longitude': float(lon),
            'manager_ids': manager_ids,
        }


def _build_phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Pastdagi tugmani bosing 👇",
    )


def _build_location_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Hozirgi lokatsiyangizni yuborish", request_location=True)],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


@router.message(StateFilter("*"), CommandStart(deep_link=True, magic=F.args.startswith("login_")))
async def cmd_start_login_deeplink(message: Message, command: CommandObject, state: FSMContext):
    """Saytdan kelgan /start login_<token> deep-link orqali telefon raqamini tasdiqlashni boshlash"""
    await state.clear()
    if not message.from_user:
        return
    if message.chat and message.chat.type != 'private':
        return

    raw_args = (command.args or "").strip()
    token_value = raw_args[len("login_"):].strip()

    status = await sync_to_async(_validate_login_token)(token_value, message.from_user.id)

    if status == "expired":
        await message.answer(
            "⏰ <b>Kirish havolasining muddati o'tgan.</b>\n\n"
            "Iltimos, saytga qaytib <b>\"Telegram Bot orqali kirish\"</b> tugmasini qaytadan bosing.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if status == "wrong_account":
        await message.answer(
            "⛔️ <b>Bu kirish havolasi boshqa Telegram akkountga tegishli!</b>\n\n"
            "Iltimos, saytda tanlagan o'sha Telegram akkountingizdan foydalaning yoki saytda yangi kirish boshlang.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if status != "ok":
        await message.answer(
            "⚠️ <b>Kirish havolasi yaroqsiz yoki allaqachon ishlatilgan.</b>\n\n"
            "Iltimos, saytda yangi kirish havolasini yarating.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await state.set_state(LoginAuthStates.waiting_for_phone)
    await state.update_data(login_token=token_value)

    await message.answer(
        "🔐 <b>Saytga kirishni tasdiqlash</b>\n\n"
        "Buyurtma berishda siz bilan bog'lanishimiz uchun <b>O'zbekiston (+998)</b> Telegram raqamingizni tasdiqlashingiz kerak.\n\n"
        "👇 Pastdagi <b>\"📱 Telefon raqamni yuborish\"</b> tugmasini bosing.\n"
        "<i>(Faqat +998 raqamlari qabul qilinadi; qo'lda yozilgan raqam yoki boshqa odamning kontakti o'tmaydi)</i>",
        parse_mode="HTML",
        reply_markup=_build_phone_keyboard(),
    )


@router.message(LoginAuthStates.waiting_for_phone, F.text == "❌ Bekor qilish")
@router.message(LoginAuthStates.waiting_for_phone, Command("cancel"))
async def cancel_login_phone(message: Message, state: FSMContext):
    """Login telefon raqami tasdiqlash jarayonini bekor qilish"""
    await state.clear()
    await message.answer(
        "❌ <b>Saytga kirish jarayoni bekor qilindi.</b>\n\n"
        "Xohlagan vaqtingizda saytdan qayta kirish tugmasini bosishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(LoginAuthStates.waiting_for_phone, F.contact)
async def process_login_phone_contact(message: Message, state: FSMContext):
    """Faqat ReplyKeyboard request_contact=True tugmasidan kelgan 100% haqiqiy o'z O'zbekiston (+998) raqamini qabul qilish"""
    if not message.from_user:
        return

    data = await state.get_data()
    token_value = str(data.get('login_token') or '').strip()
    if not token_value:
        await state.clear()
        await message.answer(
            "⚠️ <b>Kirish sessiyasi topilmadi.</b>\n\n"
            "Iltimos, saytdan yangi kirish havolasini yarating.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    pre_status = await sync_to_async(_validate_login_token)(token_value, message.from_user.id)
    if pre_status == "expired":
        await state.clear()
        await message.answer(
            "⏰ <b>Kirish havolasining muddati o'tgan.</b>\n\n"
            "Iltimos, saytga qaytib <b>\"Telegram Bot orqali kirish\"</b> tugmasini qaytadan bosing.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    if pre_status == "wrong_account":
        await state.clear()
        await message.answer(
            "⛔️ <b>Bu kirish havolasi boshqa Telegram akkountga tegishli!</b>\n\n"
            "Iltimos, saytda tanlagan o'sha Telegram akkountingizdan foydalaning.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    if pre_status != "ok":
        await state.clear()
        await message.answer(
            "⚠️ <b>Kirish havolasi yaroqsiz yoki allaqachon ishlatilgan.</b>\n\n"
            "Iltimos, saytda yangi kirish havolasini yarating.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    is_valid, reason, normalized_phone = validate_verified_own_contact(message)
    if not is_valid:
        if reason == "non_uz_phone":
            await sync_to_async(_reject_login_token)(token_value, "non_uz_phone")
            await state.clear()
            await message.answer(
                f"⛔️ <b>Faqat O'zbekiston (+998) telefon raqamlari qabul qilinadi!</b>\n\n"
                f"Sizning raqamingiz: <code>{html.escape(normalized_phone)}</code>\n"
                f"Saytga kirish va buyurtma berish uchun faqat <b>+998</b> bilan boshlanuvchi Telegram akkountdan foydalaning.",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        rejection_texts = {
            "forwarded": (
                "⛔️ <b>Boshqa chatdan forward qilingan kontakt qabul qilinmaydi!</b>\n\n"
                "Iltimos, faqat pastdagi <b>\"📱 Telefon raqamni yuborish\"</b> tugmasini bosing."
            ),
            "not_own_contact": (
                "⛔️ <b>Boshqa odamning kontakti qabul qilinmaydi!</b>\n\n"
                "Faqat o'zingizning Telegram akkountingizga bog'langan O'zbekiston (+998) raqamini pastdagi "
                "<b>\"📱 Telefon raqamni yuborish\"</b> tugmasi orqali yuboring."
            ),
            "vcard_contact": (
                "⛔️ <b>Kontaktlar ro'yxatidan (Share Contact) yuborilgan kontakt qabul qilinmaydi!</b>\n\n"
                "Iltimos, faqat pastdagi <b>\"📱 Telefon raqamni yuborish\"</b> tugmasini bosing."
            ),
            "via_bot": (
                "⛔️ <b>Boshqa bot orqali yuborilgan xabar qabul qilinmaydi!</b>\n\n"
                "Iltimos, faqat pastdagi <b>\"📱 Telefon raqamni yuborish\"</b> tugmasini bosing."
            ),
        }
        await message.answer(
            rejection_texts.get(
                reason,
                "⛔️ <b>Telefon raqamini tasdiqlab bo'lmadi!</b>\n\n"
                "Iltimos, faqat pastdagi <b>\"📱 Telefon raqamni yuborish\"</b> tugmasini bosing.",
            ),
            parse_mode="HTML",
            reply_markup=_build_phone_keyboard(),
        )
        return

    user_data = {
        'id': message.from_user.id,
        'first_name': message.from_user.first_name or '',
        'last_name': message.from_user.last_name or '',
        'username': message.from_user.username or '',
        'phone_number': normalized_phone,
    }

    ok, status = await sync_to_async(_confirm_login_token)(token_value, user_data)
    await state.clear()

    if ok and status == "confirmed":
        await message.answer(
            f"✅ <b>Saytga kirish tasdiqlandi!</b>\n\n"
            f"📞 <b>Tasdiqlangan raqam:</b> <code>{html.escape(normalized_phone)}</code>\n\n"
            f"Endi brauzerga qaytishingiz mumkin — sahifa avtomatik yangilanadi.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if status == "non_uz_phone":
        await message.answer(
            "⛔️ <b>Faqat O'zbekiston (+998) telefon raqamlari qabul qilinadi!</b>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if status == "expired":
        await message.answer(
            "⏰ <b>Kirish havolasining muddati o'tgan.</b>\n\n"
            "Iltimos, saytga qaytib <b>\"Telegram Bot orqali kirish\"</b> tugmasini qaytadan bosing.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await message.answer(
        "⚠️ <b>Kirish havolasi yaroqsiz yoki allaqachon ishlatilgan.</b>\n\n"
        "Iltimos, saytda yangi kirish havolasini yarating.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(LoginAuthStates.waiting_for_phone, ~CommandStart(), ~Command("menu"))
async def reject_manual_login_phone(message: Message, state: FSMContext):
    """Qo'lda yozilgan raqam yoki boshqa har qanday xabarni rad etib, tugmani bosishni talab qilish"""
    data = await state.get_data()
    token_value = str(data.get('login_token') or '').strip()
    if token_value and message.from_user:
        pre_status = await sync_to_async(_validate_login_token)(token_value, message.from_user.id)
        if pre_status == "expired":
            await state.clear()
            await message.answer(
                "⏰ <b>Kirish havolasining muddati o'tgan.</b>\n\n"
                "Iltimos, saytga qaytib <b>\"Telegram Bot orqali kirish\"</b> tugmasini qaytadan bosing.",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
        if pre_status != "ok":
            await state.clear()
            await message.answer(
                "⚠️ <b>Kirish havolasi yaroqsiz yoki allaqachon ishlatilgan.</b>\n\n"
                "Iltimos, saytda yangi kirish havolasini yarating.",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

    await message.answer(
        "⛔️ <b>Qo'lda kiritilgan telefon raqami qabul qilinmaydi!</b>\n\n"
        "Iltimos, faqat pastdagi <b>\"📱 Telefon raqamni yuborish\"</b> tugmasini bosib o'z O'zbekiston (+998) Telegram raqamingizni yuboring "
        "(yoki jarayonni to'xtatish uchun <b>\"❌ Bekor qilish\"</b> ni bosing).",
        parse_mode="HTML",
        reply_markup=_build_phone_keyboard(),
    )


@router.message(StateFilter("*"), CommandStart(deep_link=True, magic=F.args.startswith("courier_")))
async def cmd_start_courier_deeplink(message: Message, command: CommandObject, state: FSMContext):
    """Saytdan kelgan /start courier_<token> deep-link orqali mijozdan lokatsiya qabul qilishni boshlash"""
    await state.clear()
    if not message.from_user:
        return

    raw_args = (command.args or "").strip()
    token_value = raw_args[len("courier_"):].strip()

    status, info = await sync_to_async(_validate_courier_token)(token_value, message.from_user.id)

    if status == "expired":
        await message.answer(
            "⏰ <b>Kuryer buyurtmasi havolasining muddati o'tgan.</b>\n\n"
            "Iltimos, saytdan yangi buyurtma rasmiylashtiring.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if status == "forbidden":
        await message.answer(
            "⛔️ <b>Bu havola boshqa foydalanuvchining buyurtmasiga tegishli.</b>\n\n"
            "Iltimos, saytda o'z Telegram akkountingiz orqali buyurtma yarating.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if status != "ok":
        await message.answer(
            "⚠️ <b>Kuryer havolasi yaroqsiz yoki allaqachon tasdiqlangan.</b>\n\n"
            "Iltimos, kerak bo'lsa saytdan yangi buyurtma bering.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await state.set_state(CourierLocationStates.waiting_for_location)
    await state.update_data(
        courier_order_pk=info['order_pk'],
        courier_token=token_value,
    )

    price_line = (
        f"💵 <b>Zapchast narxi:</b> {info['part_price_uzs']:,} so'm\n"
        if info['part_price_uzs'] > 0
        else "💵 <b>Zapchast narxi:</b> Kelishiladi\n"
    )

    await message.answer(
        f"🛵 <b>Kuryer orqali olib ketish — Buyurtma #{html.escape(info['order_id'])}</b>\n\n"
        f"📱 <b>Model:</b> {html.escape(info['phone_str'])}\n"
        f"🔧 <b>Muammo / Detal:</b> {html.escape(info['part_str'])}\n"
        f"{price_line}\n"
        f"📍 <b>Kuryer xizmati narxini aniq hisoblash uchun</b> pastdagi tugmani bosib hozirgi lokatsiyangizni yuboring 👇",
        parse_mode="HTML",
        reply_markup=_build_location_keyboard(),
    )


@router.message(CourierLocationStates.waiting_for_location, F.text == "❌ Bekor qilish")
@router.message(CourierLocationStates.waiting_for_location, Command("cancel"))
async def cancel_courier_location(message: Message, state: FSMContext):
    """Kuryer lokatsiya yuborish jarayonini bekor qilish"""
    await state.clear()
    await message.answer(
        "❌ <b>Lokatsiya yuborish bekor qilindi.</b>\n\n"
        "Xohlagan vaqtingizda saytdagi havola orqali qaytib lokatsiya yuborishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(CourierLocationStates.waiting_for_location, F.location)
async def process_courier_location(message: Message, state: FSMContext, bot: Bot):
    """Mijoz lokatsiyasini qabul qilish, masofa va kuryer narxini hisoblash, adminga va mijozga yuborish"""
    if not message.from_user or not message.location:
        return

    data = await state.get_data()
    order_pk = data.get('courier_order_pk')
    token_value = data.get('courier_token', '')

    if not order_pk:
        await state.clear()
        await message.answer(
            "⚠️ Buyurtma ma'lumoti topilmadi. Iltimos, saytdagi havolani qaytadan oching.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    pre_status = await sync_to_async(_check_pending_courier_order)(
        order_pk, token_value, message.from_user.id
    )
    if pre_status != "ok":
        await state.clear()
        err_map = {
            "expired": "⏰ Buyurtma havolasining muddati o'tgan. Iltimos, saytdan qayta buyurtma bering.",
            "forbidden": "⛔️ Bu buyurtma boshqa foydalanuvchiga tegishli.",
            "already_processed": "✅ Bu buyurtma uchun lokatsiya allaqachon qabul qilingan.",
        }
        await message.answer(
            err_map.get(pre_status, "⚠️ Buyurtma topilmadi yoki yaroqsiz."),
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    lat = float(message.location.latitude)
    lon = float(message.location.longitude)

    # Masofani bot event loopini bloklamasdan alohida thread ichida hisoblash (OSRM + Haversine fallback)
    distance_km, _source = await asyncio.to_thread(calculate_road_distance_km, lat, lon)
    delivery_fee_uzs = calculate_courier_fee_uzs(distance_km)

    fin_status, result = await sync_to_async(_finalize_courier_order)(
        order_pk=order_pk,
        token_value=token_value,
        telegram_id=message.from_user.id,
        lat=lat,
        lon=lon,
        distance_km=distance_km,
        delivery_fee_uzs=delivery_fee_uzs,
    )
    await state.clear()

    if fin_status != "ok":
        await message.answer(
            "⚠️ Buyurtmani yakunlab bo'lmadi (allaqachon tasdiqlangan yoki muddati tugagan).",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    gmaps_url = build_google_maps_url(result['latitude'], result['longitude'])
    ymaps_url = build_yandex_maps_url(result['latitude'], result['longitude'])
    tg_label = f"@{html.escape(result['tg_username'])}" if result['tg_username'] else f"ID: {result['tg_id']}"
    part_price_str = f"{result['part_price_uzs']:,} so'm" if result['has_comparison'] else "-"
    phone_line = (
        f"📞 <b>Telefon:</b> <code>{html.escape(result['phone_number'])}</code>\n"
        if result.get('phone_number')
        else ""
    )

    admin_text = (
        f"🛵 <b>YANGI KURYER BUYURTMASI! #{html.escape(result['order_id'])}</b>\n"
        f"📍 <b>Shu yerdan olib ketasiz</b>\n\n"
        f"👤 <b>Mijoz:</b> {html.escape(result['client_name'])}\n"
        f"🔗 <b>Telegram:</b> <a href=\"{html.escape(result['tg_profile_url'])}\">{tg_label}</a>\n"
        f"{phone_line}"
        f"📱 <b>Model:</b> {html.escape(result['phone_str'])}\n"
        f"🔧 <b>Muammo / Detal:</b> {html.escape(result['part_str'])}\n"
        f"💵 <b>Zapchast narxi:</b> {part_price_str}\n"
        f"📏 <b>Masofa:</b> {result['distance_km']:.2f} km\n"
        f"🛵 <b>Kuryer narxi:</b> {result['delivery_fee_uzs']:,} so'm\n"
        f"💰 <b>Jami summa:</b> <b>{result['final_total_uzs']:,} so'm</b>\n"
        f"📦 <b>Holati:</b> 🔴 Yangi ariza\n"
        f"🗺 <b>Xarita:</b> <a href=\"{gmaps_url}\">Google Maps</a> | <a href=\"{ymaps_url}\">Yandex Maps</a>"
    )
    crm_kb = build_order_action_kb(result['order_pk'], 'new')

    for aid in result['manager_ids']:
        try:
            await bot.send_message(
                chat_id=aid,
                text=admin_text,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=crm_kb,
            )
            await bot.send_location(
                chat_id=aid,
                latitude=result['latitude'],
                longitude=result['longitude'],
            )
        except Exception as exc:
            logger.warning("Failed to send courier order #%s to admin %s: %s", result['order_id'], aid, exc)

    # Mijozga yakuniy chek
    receipt_lines = [
        "✅ <b>Buyurtmangiz qabul qilindi!</b>\n",
        f"🧾 <b>Buyurtma ID:</b> <code>#{html.escape(result['order_id'])}</code>",
        f"📱 <b>Model:</b> {html.escape(result['phone_str'])}",
        f"🔧 <b>Muammo / Detal:</b> {html.escape(result['part_str'])}",
    ]
    if result['has_comparison']:
        receipt_lines.append(f"💵 <b>Zapchast narxi:</b> {result['part_price_uzs']:,} so'm")
    receipt_lines.append(
        f"🛵 <b>Kuryer xizmati ({result['distance_km']:.2f} km):</b> {result['delivery_fee_uzs']:,} so'm"
    )
    receipt_lines.append(f"💰 <b>Jami summa:</b> <b>{result['final_total_uzs']:,} so'm</b>\n")
    receipt_lines.append("Tez orada menejerimiz va kuryerimiz siz bilan Telegram orqali bog'lanadi.")

    await message.answer(
        "\n".join(receipt_lines),
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(CourierLocationStates.waiting_for_location, ~CommandStart(), ~Command("menu"))
async def prompt_location_again(message: Message):
    """Lokatsiya kutilayotgan vaqtda matn yoki boshqa xabar yuborilsa eslatma berish"""
    await message.answer(
        "📍 Iltimos, pastdagi <b>\"📍 Hozirgi lokatsiyangizni yuborish\"</b> tugmasini bosing yoki jarayonni bekor qilish uchun <b>\"❌ Bekor qilish\"</b> ni tanlang.",
        parse_mode="HTML",
        reply_markup=_build_location_keyboard(),
    )
