import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from bot.config import ADMIN_IDS
from bot.keyboards.main_menu import get_main_menu, get_cancel_menu
from bot.states.admin_states import AdminAddStates
from bot.database import BotAdmin, sync_to_async
from bot.handlers.start import is_admin

router = Router()


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Adminlar bo'limi uchun menyu"""
    keyboard = [
        [
            KeyboardButton(text="👥 Adminlar ro‘yxati"),
            KeyboardButton(text="➕ Yangi admin qo‘shish"),
        ],
        [
            KeyboardButton(text="🗑 Adminni o‘chirish"),
            KeyboardButton(text="🔙 Asosiy menyu"),
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


@router.message(F.text == "👥 Adminlar")
@router.message(F.text == "👥 Adminlar ro‘yxati")
async def admins_menu(message: Message, state: FSMContext):
    """Adminlar bo'limi bosh menyusi"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    await state.clear()
    admins = await sync_to_async(list)(BotAdmin.objects.all().order_by('-created_at'))

    text = "👑 <b>MobiPrice Bot Adminlari Boshqaruvi:</b>\n\n"
    text += f"🌟 <b>Bosh SuperAdmin ID:</b> <code>{ADMIN_IDS[0] if ADMIN_IDS else 'Konfiguratsiyada'}</code>\n\n"

    if admins:
        text += "📋 <b>Qo‘shimcha tayinlangan adminlar:</b>\n"
        for idx, a in enumerate(admins, 1):
            u_info = f"@{a.username}" if a.username else "Username yo'q"
            id_info = f"ID: <code>{a.telegram_id}</code>" if a.telegram_id else "<i>(Birinchi start bosganda bog'lanadi)</i>"
            name_info = f" ({a.full_name})" if a.full_name else ""
            text += f"{idx}. <b>{u_info}</b>{name_info}\n   └ {id_info}\n"
    else:
        text += "<i>Hozircha qo‘shimcha adminlar qo‘shilmagan.</i>\n"

    text += "\nQuyidagi amallardan birini tanlang 👇"

    await message.answer(text, reply_markup=get_admin_menu(), parse_mode="HTML")


@router.message(F.text == "➕ Yangi admin qo‘shish")
async def add_admin_start(message: Message, state: FSMContext):
    """Yangi admin kiritishni boshlash"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    await state.set_state(AdminAddStates.waiting_for_identifier)
    await message.answer(
        "✍️ <b>Yangi adminning Telegram @username yoki Telegram ID sini yuboring:</b>\n\n"
        "Masalan:\n"
        "• <code>@developer_bek</code> (yoki <code>developer_bek</code>)\n"
        "• <code>123456789</code> (agar ID si ma'lum bo'lsa)\n\n"
        "<i>Eslatma: Agar username kiritsangiz, u kishi botga kirib /start bosganida uning Telegram ID si avtomatik biriktiriladi va darhol admin bo'ladi.</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(AdminAddStates.waiting_for_identifier, F.text)
async def process_admin_identifier(message: Message, state: FSMContext):
    """Admin username yoki ID sini qabul qilish"""
    raw = message.text.strip()
    is_numeric = raw.isdigit()
    username = None
    telegram_id = None

    if is_numeric:
        telegram_id = int(raw)
        # Check if already in ADMIN_IDS
        if telegram_id in ADMIN_IDS:
            await message.answer("⚠️ Bu foydalanuvchi allaqachon bosh SuperAdmin hisoblanadi!")
            return
    else:
        username = raw.replace('@', '').strip().lower()
        if len(username) < 3:
            await message.answer("Username kamida 3 ta belgidan iborat bo‘lishi kerak. Qaytadan kiriting:")
            return

    # Check if already exists in BotAdmin
    exists = False
    if telegram_id:
        exists = await sync_to_async(BotAdmin.objects.filter(telegram_id=telegram_id).exists)()
    elif username:
        exists = await sync_to_async(BotAdmin.objects.filter(username__iexact=username).exists)()

    if exists:
        await message.answer("⚠️ Bu admin allaqachon ro‘yxatda mavjud!")
        return

    await state.update_data(username=username, telegram_id=telegram_id)
    await state.set_state(AdminAddStates.waiting_for_name)

    await message.answer(
        "👤 <b>Ushbu adminning ismi yoki izohni kiriting:</b>\n"
        "(Masalan: <i>Jamshid (Katta usta)</i> yoki shunchaki <code>-</code> qoldiring):",
        parse_mode="HTML"
    )


@router.message(AdminAddStates.waiting_for_name, F.text)
async def process_admin_name(message: Message, state: FSMContext):
    """Admin ismini saqlash va jarayonni yakunlash"""
    data = await state.get_data()
    username = data.get('username')
    telegram_id = data.get('telegram_id')
    name = message.text.strip()
    if name == '-':
        name = ""

    added_by_user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name

    await sync_to_async(BotAdmin.objects.create)(
        username=username,
        telegram_id=telegram_id,
        full_name=name,
        added_by=added_by_user
    )

    await state.clear()

    display_target = f"@{username}" if username else f"ID: {telegram_id}"
    await message.answer(
        f"✅ <b>Yangi admin muvaffaqiyatli qo‘shildi!</b>\n\n"
        f"👤 <b>Admin:</b> {display_target}\n"
        f"📝 <b>Izoh:</b> {name or 'Yo‘q'}\n"
        f"👨‍💻 <b>Qo‘shgan shaxs:</b> {added_by_user}\n\n"
        f"Endi ushbu foydalanuvchi botga /start bosib barcha adminlik imkoniyatlaridan to‘liq foydalana oladi.",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )


@router.message(F.text == "🗑 Adminni o‘chirish")
async def delete_admin_start(message: Message):
    """Adminni o'chirish uchun ro'yxat chiqarish"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    admins = await sync_to_async(list)(BotAdmin.objects.all().order_by('-created_at'))

    if not admins:
        await message.answer("O‘chirish uchun birorta ham qo‘shimcha admin mavjud emas.")
        return

    buttons = []
    for a in admins:
        title = f"❌ @{a.username}" if a.username else f"❌ ID: {a.telegram_id}"
        if a.full_name:
            title += f" ({a.full_name})"
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"del_admin:{a.id}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        "🗑 <b>O‘chirmoqchi bo‘lgan admin ustiga bosing:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("del_admin:"))
async def process_delete_admin(callback: CallbackQuery):
    """Adminni bazadan o'chirish"""
    admin_id = int(callback.data.split(":")[1])

    admin_obj = await sync_to_async(BotAdmin.objects.filter(id=admin_id).first)()
    if not admin_obj:
        await callback.answer("Admin topilmadi yoki allaqachon o'chirilgan.", show_alert=True)
        return

    user_label = f"@{admin_obj.username}" if admin_obj.username else str(admin_obj.telegram_id)
    await sync_to_async(admin_obj.delete)()

    await callback.message.edit_text(
        f"✅ <b>Admin muvaffaqiyatli o‘chirildi:</b>\n"
        f"Foydalanuvchi: <b>{user_label}</b>\n\n"
        f"Uning botdan foydalanish huquqi bekor qilindi.",
        parse_mode="HTML"
    )
    await callback.answer("Admin o'chirildi!")
