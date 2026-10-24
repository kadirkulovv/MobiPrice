import os
from datetime import datetime
from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_main_menu, get_cancel_menu
from bot.states.admin_states import ExcelImportStates
from bot.database import sync_to_async
from bot.config import BASE_DIR
from bot.handlers.start import is_admin
from core.excel_manager import export_prices_to_excel, import_prices_from_excel

router = Router()
EXCEL_TMP_DIR = BASE_DIR / 'media' / 'excel_tmp'
os.makedirs(EXCEL_TMP_DIR, exist_ok=True)


def get_excel_menu() -> ReplyKeyboardMarkup:
    """Excel boshqaruvi menyusi"""
    keyboard = [
        [
            KeyboardButton(text="📥 Excel yuklab olish (Eksport)"),
            KeyboardButton(text="📤 Excel faylni yuklash (Import)"),
        ],
        [
            KeyboardButton(text="📄 Excel shablonini olish"),
            KeyboardButton(text="🔙 Asosiy menyu"),
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


@router.message(F.text == "📁 Excel Import / Export")
async def excel_home(message: Message, state: FSMContext):
    """Excel bo'limi bosh menyusi"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    await state.clear()
    await message.answer(
        "📁 <b>Ommaviy Ma'lumot Boshqaruvi (Excel Import / Export)</b>\n\n"
        "Ushbu bo‘lim orqali bazadagi barcha brendlar, telefonlar va narxlarni yoppasiga boshqarishingiz mumkin:\n\n"
        "📥 <b>Eksport:</b> Barcha narxlarni 1 ta chiroyli Excel jadvali sifatida yuklab olish.\n"
        "📤 <b>Import:</b> Kompyuterda narxlarni o‘zgartirib qayta yuklash yoki yuzlab yangi modellarni 1 zumda kiritish.\n"
        "📄 <b>Shablon:</b> Yangi telefonlar kiritish uchun namuna shablon.\n\n"
        "Kerakli amalni tanlang 👇",
        reply_markup=get_excel_menu(),
        parse_mode="HTML"
    )


@router.message(F.text == "📥 Excel yuklab olish (Eksport)")
async def export_excel_handler(message: Message):
    """Barcha narxlarni Excel fayl ko'rinishida generatsiya qilib yuborish"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    wait_msg = await message.answer("⏳ Excel jadvali tayyorlanmoqda, iltimos kuting...")

    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
    filename = f"MobiPrice_Narxlar_{timestamp}.xlsx"
    filepath = EXCEL_TMP_DIR / filename

    try:
        await sync_to_async(export_prices_to_excel)(str(filepath))

        input_file = FSInputFile(path=str(filepath), filename=filename)
        await message.answer_document(
            document=input_file,
            caption=(
                f"📊 <b>MobiPrice Narxlar va Ehtiyot Qismlar Bazasining Excel Fayli</b>\n\n"
                f"📅 <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"💡 <i>Ushbu faylni Excel orqali ochib, narxlarni yoki qoldiq miqdorlarini tahrirlab, "
                f"qayta <b>'📤 Excel faylni yuklash (Import)'</b> orqali yuborishingiz mumkin.</i>"
            ),
            parse_mode="HTML"
        )
        await wait_msg.delete()
    except Exception as e:
        await wait_msg.edit_text(f"❌ Fayl yaratishda xatolik yuz berdi: {e}")


@router.message(F.text == "📄 Excel shablonini olish")
async def download_template_handler(message: Message):
    """Namuna shablon yuborish"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    filepath = EXCEL_TMP_DIR / "MobiPrice_Namuna_Shablon.xlsx"
    await sync_to_async(export_prices_to_excel)(str(filepath))

    input_file = FSInputFile(path=str(filepath), filename="MobiPrice_Namuna_Shablon.xlsx")
    await message.answer_document(
        document=input_file,
        caption=(
            "📄 <b>MobiPrice Excel Namuna Shablon</b>\n\n"
            "Ustunlar tartibi:\n"
            "1. <b>ID:</b> Mavjud narxni yangilash uchun ID (yangi qator bo'lsa bo'sh qoldiring)\n"
            "2. <b>Brend:</b> Apple, Samsung, Xiaomi...\n"
            "3. <b>Model Seriyasi:</b> Pro series, S series...\n"
            "4. <b>Telefon Modeli:</b> iPhone 16 Pro Max...\n"
            "5. <b>Muammo / Detal:</b> Ekran almashtirish...\n"
            "6. <b>Sifat Turi:</b> original yoki copy\n"
            "7. <b>Detal Narxi:</b> So'mda (faqat raqam)\n"
            "8. <b>Usta Haqqi:</b> So'mda (faqat raqam)\n"
            "9. <b>Ombordagi Soni:</b> 5, 10 yoki 0\n"
            "10. <b>Kafolat:</b> 6 oy, 1 yil va h.k."
        ),
        parse_mode="HTML"
    )


@router.message(F.text == "📤 Excel faylni yuklash (Import)")
async def import_excel_start(message: Message, state: FSMContext):
    """Excel fayl yuklashni so'rash"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    await state.set_state(ExcelImportStates.waiting_for_file)
    await message.answer(
        "📤 <b>Tayyorlangan Excel (.xlsx) faylini yuboring:</b>\n\n"
        "<i>Eslatma: Faylni 'Hujjat' (Document) ko‘rinishida yuboring. Baza avtomatik tarzda o‘qiladi va yangilanadi.</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(ExcelImportStates.waiting_for_file, F.document)
async def process_excel_upload(message: Message, state: FSMContext, bot: Bot):
    """Yuklangan Excel faylini qabul qilib bazaga yozish"""
    doc = message.document
    if not doc.file_name.lower().endswith(('.xlsx', '.xlsm')):
        await message.answer("⚠️ Iltimos, faqat <b>.xlsx</b> formatdagi Excel faylini yuboring!")
        return

    wait_msg = await message.answer("⚙️ Fayl qabul qilindi, ma'lumotlar bazaga kiritilmoqda...")

    dest_path = EXCEL_TMP_DIR / f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{doc.file_name}"

    try:
        file = await bot.get_file(doc.file_id)
        await bot.download_file(file.file_path, dest_path)

        # Process import
        res = await sync_to_async(import_prices_from_excel)(str(dest_path))

        await state.clear()

        err_text = ""
        if res['errors']:
            err_text = f"\n⚠️ <b>Xatoliklar ({len(res['errors'])} ta):</b>\n" + "\n".join(res['errors'][:5])
            if len(res['errors']) > 5:
                err_text += f"\n... va yana {len(res['errors']) - 5} ta xatolik."

        await wait_msg.edit_text(
            f"✅ <b>Excel Ommaviy Yuklash Yakunlandi!</b>\n\n"
            f"🆕 <b>Yangi qo‘shilgan narxlar:</b> {res['created']} ta\n"
            f"✏️ <b>Yangilangan narxlar:</b> {res['updated']} ta\n"
            f"{err_text}\n\n"
            f"Barcha yangi narxlar sayt kalkulyatorida darhol faollashdi!",
            reply_markup=get_excel_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        await wait_msg.edit_text(f"❌ Faylni o‘qishda xatolik yuz berdi: {e}")
