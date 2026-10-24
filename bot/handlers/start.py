from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.config import ADMIN_IDS
from bot.keyboards.main_menu import get_main_menu, get_section_crud_menu
from bot.database import (
    Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison,
    ServiceOrder, TeamMember, BotAdmin, sync_to_async
)

router = Router()


@sync_to_async
def check_admin_access_db(user_id: int, username: str = None) -> bool:
    """Foydalanuvchi admin ekanligini bazadan va sozlamalardan tekshirish"""
    if ADMIN_IDS and user_id in ADMIN_IDS:
        return True

    # 1. Telegram ID bo'yicha tekshirish
    if BotAdmin.objects.filter(telegram_id=user_id).exists():
        return True

    # 2. Username bo'yicha tekshirish (agar @username bilan kiritilgan bo'lsa)
    if username:
        clean_user = username.replace('@', '').strip().lower()
        matched_admin = BotAdmin.objects.filter(username__iexact=clean_user).first()
        if matched_admin:
            # Telegram ID sini avtomatik biriktirib qo'yamiz
            if not matched_admin.telegram_id:
                matched_admin.telegram_id = user_id
                matched_admin.save(update_fields=['telegram_id'])
            return True

    return False


async def is_admin(user_id: int, username: str = None) -> bool:
    return await check_admin_access_db(user_id, username)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start komandasi va admin tekshiruvi"""
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username

    has_access = await is_admin(user_id, username)
    if not has_access:
        await message.answer(
            f"⛔️ <b>Ruxsat yo‘q!</b>\n\n"
            f"Assalomu alaykum, {message.from_user.full_name}!\n"
            f"Ushbu bot faqat <b>MobiPrice</b> adminlari uchun mo‘ljallangan.\n\n"
            f"Sizning Telegram ID: <code>{user_id}</code>\n"
            f"Username: @{username or 'mavjud emas'}\n\n"
            f"Botdan foydalanish uchun Telegram ID yoki username'ingizni bosh adminga yuboring.",
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"👑 <b>MobiPrice Boshqaruv Paneliga Xush Kelibsiz!</b>\n\n"
        f"Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        f"Ushbu bot orqali saytning barcha bo‘limlarini to‘liq boshqarishingiz mumkin:\n"
        f"1️⃣ <b>Brendlar</b> (Apple, Samsung, Xiaomi...)\n"
        f"2️⃣ <b>Modellar</b> (Pro seriya, S seriya...)\n"
        f"3️⃣ <b>Telefonlar</b> (iPhone 16 Pro Max, S24 Ultra...)\n"
        f"4️⃣ <b>Muammolar</b> (30 ta maxsus vektor ikonka bilan)\n"
        f"5️⃣ <b>Solishtirish</b> (Original va dublikat narxlari)\n"
        f"6️⃣ <b>Ustalar (Jamoa)</b> (Mutaxassislar va ustalar vitrinasi)\n"
        f"7️⃣ <b>Adminlar</b> (Yangi admin qo‘shish va boshqarish)\n\n"
        f"Kerakli bo‘limni tanlang 👇",
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
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    b_count = await sync_to_async(Brand.objects.count)()
    s_count = await sync_to_async(DeviceSeries.objects.count)()
    p_count = await sync_to_async(DevicePhone.objects.count)()
    i_count = await sync_to_async(DeviceIssue.objects.count)()
    c_count = await sync_to_async(IssueComparison.objects.count)()
    o_count = await sync_to_async(ServiceOrder.objects.count)()
    m_count = await sync_to_async(TeamMember.objects.count)()
    a_count = await sync_to_async(BotAdmin.objects.count)()

    await message.answer(
        f"📊 <b>MobiPrice Tizim Statistikasi:</b>\n\n"
        f"🏷 <b>Brendlar:</b> {b_count} ta\n"
        f"📂 <b>Model seriyalari:</b> {s_count} ta\n"
        f"📱 <b>Telefonlar:</b> {p_count} ta\n"
        f"🔧 <b>Muammolar / Detallar:</b> {i_count} ta\n"
        f"⚖️ <b>Solishtirish variantlari:</b> {c_count} ta\n"
        f"👨‍🔧 <b>Jamoa ustalari:</b> {m_count} ta\n"
        f"👥 <b>Qo'shimcha adminlar:</b> {a_count} ta\n"
        f"📦 <b>Kelib tushgan arizalar:</b> {o_count} ta\n",
        parse_mode="HTML"
    )


@router.message(Command("backup"))
@router.message(F.text == "💾 Zaxira (Backup)")
async def trigger_manual_backup(message: Message, bot: Bot):
    """Admin buyrug'i orqali tezkor zaxira nusxasini yuborish"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    from core.backup_service import send_backup_to_admins

    wait_msg = await message.answer("⏳ <i>Ma'lumotlar bazasi zaxira nusxasi (Gzip) tayyorlanmoqda...</i>", parse_mode="HTML")
    res = await send_backup_to_admins(bot, trigger=f"Qo‘lda so‘raldi (@{message.from_user.username or message.from_user.id})")

    if res.get('success'):
        try:
            await wait_msg.delete()
        except Exception:
            pass
    else:
        await wait_msg.edit_text(f"❌ Zaxira nusxasini olishda xatolik: {res.get('error')}")


