import html
from django.db.models import Q
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.main_menu import get_cancel_menu
from bot.database import ServiceOrder, TeamMember, sync_to_async
from bot.permissions import get_user_permissions
from core.maintenance import expire_stale_pending_courier_orders

router = Router()


async def check_crm_access(message_or_call) -> bool:
    """Faqat zayavkalar huquqiga ega bo'lganlar (Menejer, Superadmin, Both) uchun ruxsat"""
    user = message_or_call.from_user
    perms = await get_user_permissions(user.id, user.username)
    if not perms.can_handle_leads:
        denial = (
            "⛔️ <b>Ruxsat yo‘q!</b>\n\n"
            "Buyurtmalar (CRM) bo‘limi faqat <b>Menejerlar</b> va <b>Bosh Admin</b> uchun mo‘ljallangan.\n"
            "Sizning vazifangiz sayt resurslarini boshqarishdan iborat."
        )
        if isinstance(message_or_call, Message):
            await message_or_call.answer(denial, parse_mode="HTML")
        elif isinstance(message_or_call, CallbackQuery):
            await message_or_call.answer("Ruxsat yo'q! Bu bo'lim faqat menejerlar uchun.", show_alert=True)
        return False
    return True


class OrderSearchStates(StatesGroup):
    waiting_for_query = State()


def get_crm_menu() -> ReplyKeyboardMarkup:
    """CRM bo'limi bosh menyusi"""
    keyboard = [
        [
            KeyboardButton(text="🔴 Yangi arizalar"),
            KeyboardButton(text="⏳ Jarayondagilar"),
        ],
        [
            KeyboardButton(text="✅ Tayyor bo‘lganlar"),
            KeyboardButton(text="🔍 Buyurtma qidirish"),
        ],
        [
            KeyboardButton(text="🔙 Asosiy menyu"),
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def build_order_action_kb(order_id: int, current_status: str) -> InlineKeyboardMarkup:
    """Buyurtma ostidagi tezkor boshqaruv inline tugmalari"""
    buttons = []

    if current_status == 'pending_location':
        buttons.append([
            InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"crm_st:{order_id}:contacted"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"crm_st:{order_id}:cancelled"),
        ])
    elif current_status == 'new':
        buttons.append([
            InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"crm_st:{order_id}:contacted"),
            InlineKeyboardButton(text="👨‍🔧 Ustaga biriktirish", callback_data=f"crm_assign:{order_id}"),
        ])
        buttons.append([
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"crm_st:{order_id}:cancelled")
        ])
    elif current_status in ('contacted', 'in_progress'):
        buttons.append([
            InlineKeyboardButton(text="👨‍🔧 Ustaga biriktirish", callback_data=f"crm_assign:{order_id}"),
            InlineKeyboardButton(text="🎉 Tayyor deb belgilash", callback_data=f"crm_st:{order_id}:ready"),
        ])
        buttons.append([
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"crm_st:{order_id}:cancelled")
        ])
    elif current_status == 'ready':
        buttons.append([
            InlineKeyboardButton(text="📦 Topshirildi (Arxiv)", callback_data=f"crm_st:{order_id}:completed"),
            InlineKeyboardButton(text="↩️ Qayta jarayonga", callback_data=f"crm_st:{order_id}:in_progress"),
        ])
    else:  # cancelled or completed
        buttons.append([
            InlineKeyboardButton(text="🔄 Qayta tiklash", callback_data=f"crm_st:{order_id}:new")
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_order_card(order: ServiceOrder) -> str:
    """Buyurtma kartasi matni"""
    phone_name = html.escape(order.phone.name) if order.phone else "Smartfon"
    if order.comparison:
        issue_part = order.comparison.issue.title if getattr(order.comparison, 'issue', None) else ""
        comp_title = order.comparison.title
        issue_name = html.escape(f"{issue_part} ({comp_title})" if issue_part else comp_title)
        part_price_val = f"{int(order.comparison.total_price_uzs):,} so'm"
    else:
        issue_name = "Umumiy konsultatsiya"
        part_price_val = "-"

    tg_line = ""
    if order.telegram_user_id and order.telegram_user:
        tg_user = order.telegram_user
        tg_label = f"@{html.escape(tg_user.username)}" if tg_user.username else f"ID: {tg_user.telegram_id}"
        tg_line = f"🔗 <b>Telegram:</b> <a href=\"{html.escape(tg_user.tg_profile_url)}\">{tg_label}</a>\n"

    effective_phone = order.phone_number or (
        order.telegram_user.phone_number
        if order.telegram_user_id and order.telegram_user
        else ""
    )
    phone_num_line = (
        f"📞 <b>Telefon:</b> <code>{html.escape(effective_phone)}</code>\n"
        if effective_phone
        else ""
    )

    courier_lines = ""
    if order.distance_km is not None:
        courier_lines += f"📏 <b>Masofa:</b> {order.distance_km:.2f} km\n"
    if order.delivery_fee_uzs is not None:
        courier_lines += f"🛵 <b>Kuryer narxi:</b> {int(order.delivery_fee_uzs):,} so'm\n"

    if order.final_total_uzs is not None:
        total_line = f"💰 <b>Jami summa:</b> <b>{int(order.final_total_uzs):,} so'm</b>\n"
    else:
        total_line = ""

    location_line = ""
    if order.has_location:
        location_line = (
            f"🗺 <b>Lokatsiya:</b> "
            f"<a href=\"{html.escape(order.client_google_maps_url)}\">Google Maps</a> | "
            f"<a href=\"{html.escape(order.client_yandex_maps_url)}\">Yandex Maps</a>\n"
        )

    master_name = (
        f"👨‍🔧 <b>Usta:</b> {html.escape(order.master.full_name)}\n"
        if order.master
        else "👨‍🔧 <b>Usta:</b> <i>Biriktirilmagan</i>\n"
    )
    notes_line = f"📝 <b>Izoh:</b> {html.escape(order.notes)}\n" if order.notes else ""
    admin_notes_line = f"📌 <b>Qayd:</b> <i>{html.escape(order.admin_notes)}</i>\n" if order.admin_notes else ""

    status_icons = {
        'pending_location': '📍 Lokatsiya kutilmoqda',
        'new': '🔴 Yangi ariza',
        'contacted': '🟡 Bog‘lanildi (Diagnostikada)',
        'in_progress': '🔧 Ta’mirlanmoqda',
        'ready': '✅ Tayyor (Olib ketishga)',
        'completed': '📦 Mijozga topshirildi',
        'cancelled': '❌ Bekor qilindi'
    }
    status_label = status_icons.get(order.status, str(order.get_status_display()))

    return (
        f"📱 <b>BUYURTMA #{html.escape(order.order_id)}</b>\n\n"
        f"👤 <b>Mijoz:</b> {html.escape(order.client_name)}\n"
        f"{tg_line}"
        f"{phone_num_line}"
        f"📱 <b>Model:</b> {phone_name}\n"
        f"🔧 <b>Xizmat:</b> {issue_name}\n"
        f"💵 <b>Zapchast narxi:</b> {part_price_val}\n"
        f"{courier_lines}"
        f"{total_line}"
        f"📍 <b>Format:</b> {html.escape(str(order.get_service_type_display()))}\n"
        f"{location_line}"
        f"{master_name}"
        f"{notes_line}"
        f"{admin_notes_line}"
        f"📊 <b>Holati:</b> {status_label}\n"
        f"🕒 <b>Vaqti:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )


@router.message(F.text == "📦 Buyurtmalar (CRM)")
async def crm_home(message: Message, state: FSMContext):
    """CRM bosh menyusi"""
    if not await check_crm_access(message):
        return

    await state.clear()
    await sync_to_async(expire_stale_pending_courier_orders)()
    pending_loc_cnt = await sync_to_async(ServiceOrder.objects.filter(status='pending_location').count)()
    new_cnt = await sync_to_async(ServiceOrder.objects.filter(status='new').count)()
    prog_cnt = await sync_to_async(ServiceOrder.objects.filter(status__in=['contacted', 'in_progress']).count)()
    ready_cnt = await sync_to_async(ServiceOrder.objects.filter(status='ready').count)()

    pending_line = f"• 📍 <b>Lokatsiya kutilmoqda:</b> {pending_loc_cnt} ta\n" if pending_loc_cnt else ""
    await message.answer(
        f"📦 <b>MobiPrice Buyurtmalar Mini-CRM Paneli</b>\n\n"
        f"📊 <b>Arizalar holati:</b>\n"
        f"{pending_line}"
        f"• 🔴 <b>Yangi arizalar:</b> {new_cnt} ta\n"
        f"• ⏳ <b>Ta’mirlanayotganlar:</b> {prog_cnt} ta\n"
        f"• ✅ <b>Olib ketishga tayyor:</b> {ready_cnt} ta\n\n"
        f"Kerakli bo‘limni tanlang 👇",
        reply_markup=get_crm_menu(),
        parse_mode="HTML"
    )


@router.message(F.text == "🔴 Yangi arizalar")
async def list_new_orders(message: Message):
    """Yangi arizalar ro'yxati"""
    if not await check_crm_access(message):
        return

    orders = await sync_to_async(list)(
        ServiceOrder.objects.filter(status='new')
        .select_related('telegram_user', 'phone', 'comparison', 'comparison__issue', 'master')
        .order_by('-created_at')[:8]
    )

    if not orders:
        await message.answer("🎉 Hozircha yangi ko‘rilmagan arizalar yo‘q!")
        return

    for o in orders:
        text = format_order_card(o)
        kb = build_order_action_kb(o.id, o.status)
        await message.answer(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text == "⏳ Jarayondagilar")
async def list_in_progress_orders(message: Message):
    """Hozir ta'mirlanayotgan arizalar"""
    if not await check_crm_access(message):
        return

    orders = await sync_to_async(list)(
        ServiceOrder.objects.filter(status__in=['contacted', 'in_progress'])
        .select_related('telegram_user', 'phone', 'comparison', 'comparison__issue', 'master')
        .order_by('-created_at')[:8]
    )

    if not orders:
        await message.answer("Hozirda ta’mirlanish jarayonidagi arizalar mavjud emas.")
        return

    for o in orders:
        text = format_order_card(o)
        kb = build_order_action_kb(o.id, o.status)
        await message.answer(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text == "✅ Tayyor bo‘lganlar")
async def list_ready_orders(message: Message):
    """Tayyor bo'lgan arizalar"""
    if not await check_crm_access(message):
        return

    orders = await sync_to_async(list)(
        ServiceOrder.objects.filter(status='ready')
        .select_related('telegram_user', 'phone', 'comparison', 'comparison__issue', 'master')
        .order_by('-created_at')[:8]
    )

    if not orders:
        await message.answer("Tayyor holatdagi arizalar yo‘q.")
        return

    for o in orders:
        text = format_order_card(o)
        kb = build_order_action_kb(o.id, o.status)
        await message.answer(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text == "🔍 Buyurtma qidirish")
async def search_order_start(message: Message, state: FSMContext):
    """Buyurtma qidirishni boshlash"""
    if not await check_crm_access(message):
        return

    await state.set_state(OrderSearchStates.waiting_for_query)
    await message.answer(
        "🔍 <b>Buyurtma kodini (#MP-XXXXXX), mijoz ismini, @username yoki telefon raqamini kiriting:</b>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(OrderSearchStates.waiting_for_query, F.text)
async def process_order_search(message: Message, state: FSMContext):
    """Qidiruv natijalarini ko'rsatish"""
    if not await check_crm_access(message):
        return
    query = message.text.replace('#', '').strip()
    username_query = query.lstrip('@').strip()
    await state.clear()
    await sync_to_async(expire_stale_pending_courier_orders)()

    search_filter = (
        Q(order_id__icontains=query)
        | Q(phone_number__icontains=query)
        | Q(telegram_user__phone_number__icontains=query)
        | Q(client_name__icontains=query)
    )
    if username_query:
        search_filter |= Q(telegram_user__username__icontains=username_query)
    if query.isdigit():
        search_filter |= Q(telegram_user__telegram_id=int(query))

    orders = await sync_to_async(list)(
        ServiceOrder.objects.filter(search_filter)
        .select_related('telegram_user', 'phone', 'comparison', 'comparison__issue', 'master')
        .order_by('-created_at')[:5]
    )

    if not orders:
        await message.answer(
            f"❌ <b>'{html.escape(query)}'</b> bo‘yicha hech qanday buyurtma topilmadi.",
            reply_markup=get_crm_menu(),
            parse_mode="HTML"
        )
        return

    await message.answer(f"🔍 <b>Qidiruv natijalari ({len(orders)} ta):</b>", reply_markup=get_crm_menu(), parse_mode="HTML")
    for o in orders:
        text = format_order_card(o)
        kb = build_order_action_kb(o.id, o.status)
        await message.answer(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


# --- Callbacks: Status Updates & Master Assignment ---

@router.callback_query(F.data.startswith("crm_st:"))
async def process_crm_status_change(callback: CallbackQuery):
    """Buyurtma holatini bitta tugma bilan o'zgartirish"""
    if not await check_crm_access(callback):
        return
    parts = callback.data.split(":")
    order_id = int(parts[1])
    new_status = parts[2]

    order = await sync_to_async(
        ServiceOrder.objects.filter(id=order_id)
        .select_related('telegram_user', 'phone', 'comparison', 'comparison__issue', 'master')
        .first
    )()

    if not order:
        await callback.answer("Buyurtma topilmadi.", show_alert=True)
        return

    order.status = new_status
    admin_name = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    order.admin_notes = f"Holat o'zgardi: {new_status} ({admin_name})"
    await sync_to_async(order.save)(update_fields=['status', 'admin_notes'])

    updated_text = format_order_card(order)
    updated_kb = build_order_action_kb(order.id, order.status)

    try:
        await callback.message.edit_text(
            updated_text,
            reply_markup=updated_kb,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    except Exception:
        pass

    await callback.answer(f"Holat o'zgartirildi: {order.get_status_display()}")


@router.callback_query(F.data.startswith("crm_assign:"))
async def process_crm_assign_start(callback: CallbackQuery):
    """Ustalar ro'yxatini chiqarish"""
    if not await check_crm_access(callback):
        return
    order_id = int(callback.data.split(":")[1])
    masters = await sync_to_async(list)(TeamMember.objects.filter(is_active=True).order_by('order'))

    if not masters:
        await callback.answer("Bazada faol ustalar yo'q. Avval 'Ustalar (Jamoa)' bo'limidan usta qo'shing.", show_alert=True)
        return

    buttons = []
    for m in masters:
        buttons.append([InlineKeyboardButton(text=f"👨‍🔧 {m.full_name} ({m.role})", callback_data=f"crm_set_m:{order_id}:{m.id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Bekor qilish", callback_data=f"crm_refresh:{order_id}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer("Ustani tanlang")


@router.callback_query(F.data.startswith("crm_set_m:"))
async def process_crm_set_master(callback: CallbackQuery):
    """Buyurtmaga aniq ustani biriktirish"""
    if not await check_crm_access(callback):
        return
    parts = callback.data.split(":")
    order_id = int(parts[1])
    master_id = int(parts[2])

    order = await sync_to_async(
        ServiceOrder.objects.filter(id=order_id)
        .select_related('telegram_user', 'phone', 'comparison', 'comparison__issue')
        .first
    )()
    master = await sync_to_async(TeamMember.objects.filter(id=master_id).first)()

    if not order or not master:
        await callback.answer("Xatolik: usta yoki buyurtma topilmadi.", show_alert=True)
        return

    order.master = master
    order.status = 'in_progress'  # Automatically set to in_progress
    admin_name = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    order.admin_notes = f"Ustaga biriktirildi: {master.full_name} ({admin_name})"
    await sync_to_async(order.save)(update_fields=['master', 'status', 'admin_notes'])

    updated_text = format_order_card(order)
    updated_kb = build_order_action_kb(order.id, order.status)

    try:
        await callback.message.edit_text(
            updated_text,
            reply_markup=updated_kb,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    except Exception:
        pass

    await callback.answer(f"Usta biriktirildi: {master.full_name}")


@router.callback_query(F.data.startswith("crm_refresh:"))
async def process_crm_refresh(callback: CallbackQuery):
    """Buyurtma menyusini dastlabki holatga qaytarish"""
    if not await check_crm_access(callback):
        return
    order_id = int(callback.data.split(":")[1])
    order = await sync_to_async(
        ServiceOrder.objects.filter(id=order_id)
        .select_related('telegram_user', 'phone', 'comparison', 'comparison__issue', 'master')
        .first
    )()
    if order:
        kb = build_order_action_kb(order.id, order.status)
        await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()
