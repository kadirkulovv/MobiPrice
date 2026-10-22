import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, Document
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_section_crud_menu, get_cancel_menu
from bot.keyboards.common import build_3_row_inline_kb
from bot.states.admin_states import BrandAddStates
from bot.database import Brand, sync_to_async
from bot.config import MEDIA_BRANDS_DIR, BASE_DIR

router = Router()


@router.message(F.text == "🏷 Brendlar")
async def brands_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏷 <b>Brendlar bo‘limi</b>\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=get_section_crud_menu("Brend"),
        parse_mode="HTML"
    )


@router.message(F.text == "📋 Brend ro‘yxati")
async def list_brands(message: Message):
    brands = await sync_to_async(list)(Brand.objects.all().order_by('order', 'name'))

    if not brands:
        await message.answer("Bazada hozircha birorta ham brend mavjud emas.")
        return

    text = "📋 <b>Mavjud Brendlar ro‘yxati:</b>\n\n"
    for idx, b in enumerate(brands, 1):
        logo_info = "✅ SVG bor" if b.logo else "❌ Logo yo'q"
        text += f"{idx}. <b>{b.name}</b> (slug: <code>{b.slug}</code>) — {logo_info}\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "➕ Yangi Brend qo‘shish")
async def add_brand_start(message: Message, state: FSMContext):
    await state.set_state(BrandAddStates.waiting_for_name)
    await message.answer(
        "✍️ <b>Yangi brend nomini kiriting:</b>\n"
        "(Masalan: <i>Apple</i>, <i>Samsung</i>, <i>Xiaomi</i>, <i>Google Pixel</i>)",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(BrandAddStates.waiting_for_name, F.text)
async def process_brand_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Brend nomi kamida 2 ta harfdan iborat bo‘lishi kerak. Qaytadan kiriting:")
        return

    exists = await sync_to_async(Brand.objects.filter(name__iexact=name).exists)()
    if exists:
        await message.answer(f"⚠️ '{name}' nomli brend allaqachon mavjud! Boshqa nom kiriting:")
        return

    await state.update_data(brand_name=name)
    await state.set_state(BrandAddStates.waiting_for_logo)

    await message.answer(
        f"✅ Brend nomi: <b>{name}</b>\n\n"
        f"Endi ushbu brendning <b>.svg</b> formatidagi logotip faylini yuboring:\n"
        f"<i>(Telegramga fayl/hujjat sifatida yuklang)</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(BrandAddStates.waiting_for_logo, F.document)
async def process_brand_logo(message: Message, state: FSMContext, bot: Bot):
    doc: Document = message.document
    if not doc.file_name.lower().endswith(('.svg', '.png', '.jpg', '.jpeg')):
        await message.answer("⚠️ Iltimos, faqat <b>.svg</b> (yoki .png) formatidagi fayl yuboring:")
        return

    data = await state.get_data()
    brand_name = data.get('brand_name')

    # Download file to media/brands/
    file = await bot.get_file(doc.file_id)
    ext = os.path.splitext(doc.file_name)[1].lower() or '.svg'
    safe_slug = brand_name.lower().replace(' ', '_')
    save_filename = f"{safe_slug}{ext}"
    dest_path = MEDIA_BRANDS_DIR / save_filename

    await bot.download_file(file.file_path, destination=dest_path)

    # Save to database
    rel_path = f"brands/{save_filename}"
    brand = await sync_to_async(Brand.objects.create)(
        name=brand_name,
        logo=rel_path
    )

    await state.clear()
    await message.answer(
        f"🎉 <b>Yangi brend muvaffaqiyatli saqlandi!</b>\n\n"
        f"🏷 Nomi: <b>{brand.name}</b>\n"
        f"📁 Fayl: <code>{save_filename}</code>",
        reply_markup=get_section_crud_menu("Brend"),
        parse_mode="HTML"
    )


@router.message(F.text == "🗑 Brend o‘chirish")
async def delete_brand_start(message: Message):
    brands = await sync_to_async(list)(Brand.objects.all().order_by('name'))
    if not brands:
        await message.answer("O‘chirish uchun brendlar mavjud emas.")
        return

    items = [(b.name, f"del_brand_{b.id}") for b in brands]
    kb = build_3_row_inline_kb(items, back_callback="", add_cancel=True)

    await message.answer(
        "🗑 <b>O‘chirmoqchi bo‘lgan brendingizni tanlang:</b>\n"
        "<i>Eslatma: Brend o‘chirilsa, unga tegishli barcha modellar ham o‘chadi!</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("del_brand_"))
async def process_delete_brand(call: CallbackQuery):
    brand_id = int(call.data.replace("del_brand_", ""))
    try:
        brand = await sync_to_async(Brand.objects.get)(id=brand_id)
        name = brand.name
        await sync_to_async(brand.delete)()
        await call.message.edit_text(f"✅ <b>{name}</b> brendi muvaffaqiyatli o‘chirildi!", parse_mode="HTML")
    except Exception as e:
        await call.message.edit_text(f"Xatolik: {e}")
    await call.answer()


@router.callback_query(F.data == "cancel_action")
async def cancel_inline(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Amal bekor qilindi.")
    await call.answer()
