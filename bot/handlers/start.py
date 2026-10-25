from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.config import ADMIN_IDS
from bot.keyboards.main_menu import get_main_menu, get_section_crud_menu
from bot.permissions import get_user_permissions, UserPermissions
from bot.database import (
    Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison,
    ServiceOrder, TeamMember, BotAdmin, sync_to_async
)

router = Router()


async def is_admin(user_id: int, username: str = None) -> bool:
    """Umumiy kirish huquqi mavjudligini tekshirish (Admin, Menejer yoki Superadmin)"""
    perms = await get_user_permissions(user_id, username)
    return perms.has_any_access


async def is_site_admin(user_id: int, username: str = None) -> bool:
    """Sayt resurslarini boshqarish huquqini tekshirish (Admin, Superadmin, Both)"""
    perms = await get_user_permissions(user_id, username)
    return perms.can_manage_site


@router.message(CommandStart())
@router.message(F.text == "🔄 Yangilash")
async def cmd_start(message: Message, state: FSMContext):
    """Start komandasi va rolga mos panelni ochish"""
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username

    perms: UserPermissions = await get_user_permissions(user_id, username)
    if not perms.has_any_access:
        await message.answer(
            f"⛔️ <b>Ruxsat yo‘q!</b>\n\n"
            f"Assalomu alaykum, {message.from_user.full_name}!\n"
            f"Ushbu bot faqat <b>MobiPrice</b> admin va menejerlari uchun mo‘ljallangan.\n\n"
            f"Sizning Telegram ID: <code>{user_id}</code>\n"
            f"Username: @{username or 'mavjud emas'}\n\n"
            f"Botdan foydalanish uchun Telegram ID yoki username'ingizni Bosh Adminga yuboring.",
            parse_mode="HTML"
        )
        return

    # Rolga mos tavsif xabari
    if perms.is_superadmin:
        desc = (
            "👑 <b>Bosh Admin (Superadmin) Paneli:</b>\n\n"
            "Sizda tizim bo‘yicha to‘liq cheklovsiz huquqlar mavjud:\n"
            "• 📦 <b>Zayavkalar (CRM):</b> Mijozlar arizalari va konsultatsiyalar\n"
            "• 🛠 <b>Sayt resurslari:</b> Brendlar, modellar, narxlar, ustalar, Excel\n"
            "• 👥 <b>Xodimlar:</b> Yangi admin va menejerlar qo‘shish/o‘chirish\n"
            "• 💾 <b>Zaxira:</b> SQLite bazani arxivlash va yuklab olish"
        )
    elif perms.role == 'both':
        desc = (
            "🌟 <b>Admin + Menejer Paneli:</b>\n\n"
            "Sizga sayt resurslari va buyurtmalar bo‘yicha to‘liq ruxsat berilgan:\n"
            "• 📦 <b>Zayavkalar (CRM):</b> Buyurtmalar bilan ishlash\n"
            "• 🛠 <b>Sayt resurslari:</b> Brendlar, modellar, narxlar, ustalar, Excel\n"
            "<i>(Eslatma: Yangi admin qo‘shish faqat Bosh Admin vakolatida)</i>"
        )
    elif perms.role == 'admin':
        desc = (
            "🛠️ <b>Sayt Administratori Paneli:</b>\n\n"
            "Siz sayt resurslarini to‘liq boshqarishingiz mumkin:\n"
            "• 🏷 <b>Brendlar, Modellar, Telefonlar</b>\n"
            "• 🔧 <b>Muammolar va Narxlar (Solishtirish)</b>\n"
            "• 📁 <b>Excel Import / Export</b>\n"
            "• 👨‍🔧 <b>Ustalar va mutaxassislar vitrinasi</b>\n"
            "<i>(Zayavkalar faqat menejerlarga keladi)</i>"
        )
    else:  # manager
        desc = (
            "📋 <b>Menejer Paneli:</b>\n\n"
            "Siz mijozlardan kelib tushadigan zayavkalarni qabul qilasiz va CRM da ishlaysiz:\n"
            "• 📦 <b>Buyurtmalar (CRM):</b> Yangi arizalar, mijozlar bilan bog‘lanish, holatni yangilash\n"
            "• 📊 <b>Statistika:</b> Buyurtmalar soni va hisoboti"
        )

    await message.answer(
        f"{desc}\n\n"
        f"Xush kelibsiz, <b>{message.from_user.first_name}</b>! Kerakli bo‘limni tanlang 👇",
        reply_markup=get_main_menu(perms),
        parse_mode="HTML"
    )


@router.message(F.text == "🔙 Asosiy menyu")
@router.message(F.text == "❌ Bekor qilish")
async def back_to_main(message: Message, state: FSMContext):
    """Har qanday holatdan asosiy menyuga qaytish"""
    await state.clear()
    perms = await get_user_permissions(message.from_user.id, message.from_user.username)
    await message.answer(
        "🏠 Asosiy menyuga qaytdingiz. Kerakli bo‘limni tanlang:",
        reply_markup=get_main_menu(perms)
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


