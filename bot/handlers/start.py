from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.config import ADMIN_IDS
from bot.keyboards.main_menu import get_main_menu, get_section_crud_menu
from bot.database import Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison, sync_to_async

router = Router()


def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    if not ADMIN_IDS:
        return True  # If no IDs configured yet, allow for initial setup
    return user_id in ADMIN_IDS


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start komandasi va admin tekshiruvi"""
    await state.clear()
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer(
            f"⛔️ <b>Ruxsat yo‘q!</b>\n\n"
            f"Assalomu alaykum, {message.from_user.full_name}!\n"
            f"Ushbu bot faqat <b>MobiPrice</b> adminlari uchun mo‘ljallangan.\n\n"
            f"Sizning Telegram ID: <code>{user_id}</code>\n"
            f"Botdan foydalanish uchun ID raqamingizni bosh adminga yuboring.",
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"👑 <b>MobiPrice Admin Paneliga Xush Kelibsiz!</b>\n\n"
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        f"Ushbu bot orqali saytning <b>5 bosqichli</b> ma'lumotlar bazasini boshqarishingiz mumkin:\n"
        f"1️⃣ <b>Brendlar</b> (Apple, Samsung, Xiaomi...)\n"
        f"2️⃣ <b>Modellar</b> (Pro seriya, S seriya...)\n"
        f"3️⃣ <b>Telefonlar</b> (iPhone 16 Pro Max, S24 Ultra...)\n"
        f"4️⃣ <b>Muammolar</b> (30 ta maxsus ikonka bilan)\n"
        f"5️⃣ <b>Solishtirish</b> (Original va dublikat narxlari)\n\n"
        f"Boshlash uchun quyidagi tugmalardan birini bosing 👇",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.message(F.text == "🔙 Asosiy menyu")
@router.message(F.text == "❌ Bekor qilish")
async def back_to_main(message: Message, state: FSMContext):
    """Har qanday holatdan asosiy menyuga qaytish"""
    await state.clear()
    await message.answer(
        "🏠 Asosiy menyuga qaytdingiz. Kerakli bo‘limni tanlang:",
        reply_markup=get_main_menu()
    )


@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    """Bazada mavjud ma'lumotlar soni"""
    if not is_admin(message.from_user.id):
        return

    b_count = await sync_to_async(Brand.objects.count)()
    s_count = await sync_to_async(DeviceSeries.objects.count)()
    p_count = await sync_to_async(DevicePhone.objects.count)()
    i_count = await sync_to_async(DeviceIssue.objects.count)()
    c_count = await sync_to_async(IssueComparison.objects.count)()

    await message.answer(
        f"📊 <b>MobiPrice Ma'lumotlar Bazasi Statistikasi:</b>\n\n"
        f"🏷 <b>Brendlar:</b> {b_count} ta\n"
        f"📂 <b>Model seriyalari:</b> {s_count} ta\n"
        f"📱 <b>Telefonlar:</b> {p_count} ta\n"
        f"🔧 <b>Muammolar / Detallar:</b> {i_count} ta\n"
        f"⚖️ <b>Solishtirish variantlari:</b> {c_count} ta\n",
        parse_mode="HTML"
    )
