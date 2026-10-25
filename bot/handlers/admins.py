import os
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.context import FSMContext
from bot.config import ADMIN_IDS
from bot.keyboards.main_menu import get_main_menu, get_cancel_menu
from bot.states.admin_states import AdminAddStates
from bot.database import BotAdmin, sync_to_async
from bot.permissions import get_user_permissions, UserPermissions

router = Router()


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Xodimlar (Admin va Menejerlar) bo'limi menyusi"""
    keyboard = [
        [
            KeyboardButton(text="👥 Xodimlar ro‘yxati"),
            KeyboardButton(text="➕ Yangi xodim qo‘shish"),
        ],
        [
            KeyboardButton(text="⚙️ Xodimni boshqarish (Rol / O‘chirish)"),
            KeyboardButton(text="🔙 Asosiy menyu"),
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


async def check_superadmin(message_or_call) -> bool:
    """Faqat Bosh Admin (Superadmin) ruxsatini tekshirish"""
    user = message_or_call.from_user
    perms: UserPermissions = await get_user_permissions(user.id, user.username)
    if not perms.is_superadmin:
        denial_text = (
            "⛔️ <b>Ruxsat yo‘q!</b>\n\n"
            "Admin va Menejerlarni qo‘shish, o‘chirish yoki ularning rollarini o‘zgartirish "
            "huquqi <b>faqat Bosh Admin (Superadmin)</b> ga tegishli!"
        )
        if isinstance(message_or_call, Message):
            await message_or_call.answer(denial_text, parse_mode="HTML")
        elif isinstance(message_or_call, CallbackQuery):
            await message_or_call.answer("Ruxsat yo'q! Faqat Bosh Admin boshqara oladi.", show_alert=True)
        return False
    return True


# =====================================================================
# 1. RO'YXAT VA BOSHQARUV BOSH SAHIFASI
# =====================================================================

@router.message(F.text.in_({"👥 Xodimlar (Admin / Menejer)", "👥 Adminlar", "👥 Xodimlar ro‘yxati", "👥 Adminlar ro‘yxati"}))
async def staff_list_view(message: Message, state: FSMContext):
    """Xodimlar ro'yxatini ko'rsatish"""
    if not await check_superadmin(message):
        return

    await state.clear()
    staff_members = await sync_to_async(list)(BotAdmin.objects.all().order_by('-created_at'))

    superadmin_id = ADMIN_IDS[0] if ADMIN_IDS else "Aniqlanmagan"

    text = (
        "👥 <b>MobiPrice Xodimlar (Admin va Menejerlar) Boshqaruvi</b>\n\n"
        f"👑 <b>Bosh SuperAdmin ID:</b> <code>{superadmin_id}</code> <i>(To‘liq cheksiz huquq)</i>\n\n"
    )

    if staff_members:
        text += "📋 <b>Tayinlangan xodimlar ro‘yxati:</b>\n"
        for idx, s in enumerate(staff_members, 1):
            u_info = f"@{s.username}" if s.username else "Username yo'q"
            id_info = f"<code>{s.telegram_id}</code>" if s.telegram_id else "<i>(Start bosganda biriktiriladi)</i>"
            name_info = f" — <b>{s.full_name}</b>" if s.full_name else ""
            status_dot = "🟢 Faol" if s.is_active else "🔴 Nofaol"

            text += (
                f"{idx}. {s.role_badge}{name_info}\n"
                f"   • Foydalanuvchi: {u_info}\n"
                f"   • Telegram ID: {id_info}\n"
                f"   • Holati: {status_dot}\n\n"
            )
    else:
        text += "<i>Hozircha qo‘shimcha xodimlar kiritilmagan.</i>\n\n"

    text += (
        "💡 <b>Rollarning vazifalari:</b>\n"
        "• 🛠 <b>Admin:</b> Faqat sayt resurslarini boshqaradi (zayavkalar bormaydi)\n"
        "• 📋 <b>Menejer:</b> Faqat zayavkalarni qabul qiladi va CRM da ishlaydi\n"
        "• 🌟 <b>Admin + Menejer:</b> Ikkala huquqqa ham ega bo‘ladi\n\n"
        "Kerakli amalni tanlang 👇"
    )

    await message.answer(text, reply_markup=get_admin_menu(), parse_mode="HTML")


# =====================================================================
# 2. YANGI XODIM QO'SHISH (3 BOSQICHLI: IDENTIFIER -> NAME -> ROLE)
# =====================================================================

@router.message(F.text.in_({"➕ Yangi xodim qo‘shish", "➕ Yangi admin qo‘shish"}))
async def add_staff_start(message: Message, state: FSMContext):
    """Yangi xodim kiritishni boshlash"""
    if not await check_superadmin(message):
        return

    await state.set_state(AdminAddStates.waiting_for_identifier)
    await message.answer(
        "✍️ <b>Yangi xodimning Telegram @username yoki Telegram ID raqamini kiriting:</b>\n\n"
        "Masalan:\n"
        "• <code>@menejer_shaxzod</code> (yoki <code>menejer_shaxzod</code>)\n"
        "• <code>123456789</code> (agar Telegram ID ma'lum bo‘lsa)\n\n"
        "<i>Eslatma: Agar @username kiritilsa, xodim botga /start bosganida uning Telegram ID si avtomatik ulanadi.</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(AdminAddStates.waiting_for_identifier, F.text)
async def process_staff_identifier(message: Message, state: FSMContext):
    """Identifier (username yoki ID) ni tekshirish va qabul qilish"""
    raw = message.text.strip()
    is_numeric = raw.isdigit()
    username = None
    telegram_id = None

    if is_numeric:
        telegram_id = int(raw)
        if telegram_id in ADMIN_IDS:
            await message.answer("⚠️ Bu foydalanuvchi allaqachon Bosh SuperAdmin hisoblanadi!")
            return
    else:
        username = raw.replace('@', '').strip().lower()
        if len(username) < 3:
            await message.answer("Username kamida 3 ta belgidan iborat bo‘lishi kerak. Qaytadan kiriting:")
            return

    # Allaqachon mavjudligini tekshirish
    exists = False
    if telegram_id:
        exists = await sync_to_async(BotAdmin.objects.filter(telegram_id=telegram_id).exists)()
    elif username:
        exists = await sync_to_async(BotAdmin.objects.filter(username__iexact=username).exists)()

    if exists:
        await message.answer("⚠️ Bu xodim allaqachon ro‘yxatda mavjud!")
        return

    await state.update_data(username=username, telegram_id=telegram_id)
    await state.set_state(AdminAddStates.waiting_for_name)

    await message.answer(
        "👤 <b>Xodimning ismi yoki izohini kiriting:</b>\n"
        "(Masalan: <i>Azizbek (Katta menejer)</i> yoki shunchaki <code>-</code> qoldiring):",
        parse_mode="HTML"
    )


@router.message(AdminAddStates.waiting_for_name, F.text)
async def process_staff_name(message: Message, state: FSMContext):
    """Ismni qabul qilish va rol tanlash tugmalarini chiqarish"""
    name = message.text.strip()
    if name == '-':
        name = ""

    await state.update_data(full_name=name)
    await state.set_state(AdminAddStates.waiting_for_role)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛠️ Faqat Admin (Sayt resurslari)", callback_data="addrole:admin"),
        ],
        [
            InlineKeyboardButton(text="📋 Faqat Menejer (Zayavkalar / CRM)", callback_data="addrole:manager"),
        ],
        [
            InlineKeyboardButton(text="🌟 Admin + Menejer (Ikkala vazifa)", callback_data="addrole:both"),
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="addrole:cancel"),
        ]
    ])

    await message.answer(
        "🎯 <b>Ushbu xodimga qanday vazifa (rol) bermoqchisiz?</b>\n\n"
        "1️⃣ 🛠️ <b>Faqat Admin:</b>\n"
        "Sayt resurslarini (brendlar, modellar, narxlar, ustalar, Excel) to‘liq boshqaradi. "
        "<b>Unga zayavkalar (buyurtmalar) bormaydi.</b>\n\n"
        "2️⃣ 📋 <b>Faqat Menejer:</b>\n"
        "Mijozlardan keladigan barcha zayavkalarni qabul qiladi va CRM da ishlaydi. "
        "Sayt resurslariga kira olmaydi.\n\n"
        "3️⃣ 🌟 <b>Admin + Menejer:</b>\n"
        "Ikkala imkoniyat ham beriladi: sayt resurslarini ham boshqaradi, buyurtmalarni ham qabul qiladi.\n\n"
        "Tugmalardan birini tanlang 👇",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(AdminAddStates.waiting_for_role, F.data.startswith("addrole:"))
async def process_staff_role(callback: CallbackQuery, state: FSMContext):
    """Rolni saqlash va jarayonni yakunlash"""
    role_choice = callback.data.split(":")[1]

    if role_choice == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Yangi xodim qo‘shish bekor qilindi.")
        await callback.answer("Bekor qilindi")
        return

    data = await state.get_data()
    username = data.get('username')
    telegram_id = data.get('telegram_id')
    name = data.get('full_name', '')

    added_by_user = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name

    new_obj = await sync_to_async(BotAdmin.objects.create)(
        username=username,
        telegram_id=telegram_id,
        full_name=name,
        role=role_choice,
        is_active=True,
        added_by=added_by_user
    )

    await state.clear()

    display_target = f"@{username}" if username else f"ID: {telegram_id}"
    await callback.message.edit_text(
        f"✅ <b>Yangi xodim muvaffaqiyatli qo‘shildi!</b>\n\n"
        f"👤 <b>Xodim:</b> {display_target}\n"
        f"📝 <b>Ismi / Izoh:</b> {name or 'Ko‘rsatilmagan'}\n"
        f"🎭 <b>Roli:</b> {new_obj.role_badge}\n"
        f"👨‍💻 <b>Qo‘shgan shaxs:</b> {added_by_user}\n\n"
        f"Endi ushbu xodim botga /start bosganida faqat o‘zining roliga mos bo‘limlarni ko‘ra oladi.",
        parse_mode="HTML"
    )
    await callback.answer("Xodim qo'shildi!")


# =====================================================================
# 3. XODIMNI BOSHQARISH (ROLNI O'ZGARTIRISH / FOALLIK / O'CHIRISH)
# =====================================================================

@router.message(F.text.in_({"⚙️ Xodimni boshqarish (Rol / O‘chirish)", "🗑 Adminni o‘chirish"}))
async def manage_staff_list(message: Message):
    """Boshqarish uchun xodimlar tugmalarini chiqarish"""
    if not await check_superadmin(message):
        return

    staff_members = await sync_to_async(list)(BotAdmin.objects.all().order_by('-created_at'))
    if not staff_members:
        await message.answer("Boshqarish uchun birorta ham qo‘shimcha xodim mavjud emas.")
        return

    buttons = []
    for s in staff_members:
        label = f"{s.role_badge} "
        label += f"@{s.username}" if s.username else f"ID: {s.telegram_id}"
        if s.full_name:
            label += f" ({s.full_name})"
        if not s.is_active:
            label += " [Nofaol]"

        buttons.append([InlineKeyboardButton(text=label, callback_data=f"staff_detail:{s.id}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        "⚙️ <b>Boshqarmoqchi bo‘lgan xodim ustiga bosing:</b>\n"
        "<i>(Rolini o‘zgartirish, vaqtincha nofaol qilish yoki butunlay o‘chirish mumkin)</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("staff_detail:"))
async def show_staff_detail(callback: CallbackQuery):
    """Xodim tafsilotlari va harakatlar kartasi"""
    if not await check_superadmin(callback):
        return

    staff_id = int(callback.data.split(":")[1])
    staff = await sync_to_async(BotAdmin.objects.filter(id=staff_id).first)()

    if not staff:
        await callback.answer("Xodim topilmadi!", show_alert=True)
        return

    user_label = f"@{staff.username}" if staff.username else f"ID: {staff.telegram_id}"
    status_text = "🟢 Faol" if staff.is_active else "🔴 Nofaol (Kirish bloklangan)"

    card_text = (
        f"👤 <b>Xodim:</b> {user_label}\n"
        f"📝 <b>Ismi:</b> {staff.full_name or 'Ko‘rsatilmagan'}\n"
        f"🎭 <b>Hozirgi roli:</b> {staff.role_badge}\n"
        f"🔘 <b>Holati:</b> {status_text}\n"
        f"📅 <b>Qo‘shilgan sana:</b> {staff.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Quyidagi amallardan birini tanlang 👇"
    )

    toggle_btn_text = "⏸ Nofaol qilish" if staff.is_active else "▶️ Faollashtirish"
    toggle_status_val = 0 if staff.is_active else 1

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛠️ Faqat Admin qilish", callback_data=f"set_staff_role:{staff.id}:admin"),
            InlineKeyboardButton(text="📋 Faqat Menejer qilish", callback_data=f"set_staff_role:{staff.id}:manager"),
        ],
        [
            InlineKeyboardButton(text="🌟 Admin + Menejer qilish", callback_data=f"set_staff_role:{staff.id}:both"),
        ],
        [
            InlineKeyboardButton(text=toggle_btn_text, callback_data=f"toggle_staff:{staff.id}:{toggle_status_val}"),
            InlineKeyboardButton(text="🗑 Butunlay o‘chirish", callback_data=f"del_staff:{staff.id}"),
        ],
        [
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="staff_back_list"),
        ]
    ])

    await callback.message.edit_text(card_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("set_staff_role:"))
async def process_change_staff_role(callback: CallbackQuery):
    """Xodim rolini o'zgartirish"""
    if not await check_superadmin(callback):
        return

    parts = callback.data.split(":")
    staff_id = int(parts[1])
    new_role = parts[2]

    staff = await sync_to_async(BotAdmin.objects.filter(id=staff_id).first)()
    if not staff:
        await callback.answer("Xodim topilmadi!", show_alert=True)
        return

    staff.role = new_role
    await sync_to_async(staff.save)(update_fields=['role'])

    await callback.answer(f"Rol o'zgartirildi: {staff.role_badge}", show_alert=True)

    # Kartani qayta ko'rsatamiz
    callback.data = f"staff_detail:{staff_id}"
    await show_staff_detail(callback)


@router.callback_query(F.data.startswith("toggle_staff:"))
async def process_toggle_staff_active(callback: CallbackQuery):
    """Xodim faolligini yoqish yoki o'chirish"""
    if not await check_superadmin(callback):
        return

    parts = callback.data.split(":")
    staff_id = int(parts[1])
    new_status = bool(int(parts[2]))

    staff = await sync_to_async(BotAdmin.objects.filter(id=staff_id).first)()
    if not staff:
        await callback.answer("Xodim topilmadi!", show_alert=True)
        return

    staff.is_active = new_status
    await sync_to_async(staff.save)(update_fields=['is_active'])

    msg = "Xodim faollashtirildi!" if new_status else "Xodim nofaol qilindi (kirish to'xtatildi)!"
    await callback.answer(msg, show_alert=True)

    callback.data = f"staff_detail:{staff_id}"
    await show_staff_detail(callback)


@router.callback_query(F.data.startswith("del_staff:"))
async def process_delete_staff(callback: CallbackQuery):
    """Xodimni bazadan o'chirish"""
    if not await check_superadmin(callback):
        return

    staff_id = int(callback.data.split(":")[1])
    staff = await sync_to_async(BotAdmin.objects.filter(id=staff_id).first)()
    if not staff:
        await callback.answer("Xodim topilmadi yoki allaqachon o'chirilgan.", show_alert=True)
        return

    user_label = f"@{staff.username}" if staff.username else str(staff.telegram_id)
    await sync_to_async(staff.delete)()

    await callback.message.edit_text(
        f"✅ <b>Xodim muvaffaqiyatli o‘chirildi:</b>\n"
        f"Foydalanuvchi: <b>{user_label}</b>\n\n"
        f"Uning botdan foydalanish huquqi butunlay bekor qilindi.",
        parse_mode="HTML"
    )
    await callback.answer("O'chirildi!")


@router.callback_query(F.data == "staff_back_list")
async def back_to_staff_list(callback: CallbackQuery):
    """Ro'yxatga qaytish"""
    staff_members = await sync_to_async(list)(BotAdmin.objects.all().order_by('-created_at'))
    if not staff_members:
        await callback.message.edit_text("Boshqarish uchun birorta ham qo‘shimcha xodim mavjud emas.")
        return

    buttons = []
    for s in staff_members:
        label = f"{s.role_badge} "
        label += f"@{s.username}" if s.username else f"ID: {s.telegram_id}"
        if s.full_name:
            label += f" ({s.full_name})"
        if not s.is_active:
            label += " [Nofaol]"

        buttons.append([InlineKeyboardButton(text=label, callback_data=f"staff_detail:{s.id}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(
        "⚙️ <b>Boshqarmoqchi bo‘lgan xodim ustiga bosing:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()
