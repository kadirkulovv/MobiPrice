import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, Document
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_section_crud_menu, get_cancel_menu
from bot.keyboards.common import build_3_row_inline_kb
from bot.states.admin_states import BrandAddStates, BrandEditStates
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


@router.message(BrandAddStates.waiting_for_logo, F.document | F.photo)
async def process_brand_logo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    brand_name = data.get('brand_name', 'brend')

    if message.document:
        doc: Document = message.document
        ext = os.path.splitext(doc.file_name)[1].lower() if doc.file_name else '.svg'
        if not ext.endswith(('.svg', '.png', '.jpg', '.jpeg', '.webp')):
            await message.answer("⚠️ Iltimos, faqat <b>.svg</b> yoki .png formatidagi fayl yuboring:", parse_mode="HTML")
            return
        file_obj = doc
    else:
        file_obj = message.photo[-1]
        ext = '.png'

    from django.utils.text import slugify
    safe_slug = slugify(brand_name).replace('-', '_')
    save_filename = f"{safe_slug}{ext}"
    dest_path = MEDIA_BRANDS_DIR / save_filename

    try:
        await bot.download(file_obj, destination=dest_path)
    except Exception as e:
        await message.answer(f"Logotipni yuklab olishda xatolik: {e}\nQaytadan yuboring:")
        return

    # Save to database
    rel_path = f"brands/{save_filename}"
    brand = await sync_to_async(Brand.objects.create)(
        name=brand_name,
        logo=rel_path
    )

    await state.clear()
    import html
    await message.answer(
        f"🎉 <b>Yangi brend muvaffaqiyatli saqlandi!</b>\n\n"
        f"🏷 Nomi: <b>{html.escape(brand.name)}</b>\n"
        f"📁 Fayl: <code>{save_filename}</code>",
        reply_markup=get_section_crud_menu("Brend"),
        parse_mode="HTML"
    )


@router.message(BrandAddStates.waiting_for_logo)
async def invalid_brand_logo(message: Message):
    await message.answer(
        "⚠️ Iltimos, brend logotipini (.svg yoki rasm fayli) yuboring:\n"
        "(Yoki '❌ Bekor qilish' tugmasini bosing)",
        reply_markup=get_cancel_menu()
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


@router.message(F.text == "✏️ Brend tahrirlash")
async def edit_brand_start(message: Message):
    brands = await sync_to_async(list)(Brand.objects.all().order_by('name'))
    if not brands:
        await message.answer("Tahrirlash uchun brendlar mavjud emas.")
        return

    items = [(b.name, f"edit_brand_{b.id}") for b in brands]
    kb = build_3_row_inline_kb(items, back_callback="", add_cancel=True)

    await message.answer(
        "✏️ <b>Tahrirlamoqchi bo‘lgan brendni tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("edit_brand_"))
async def process_select_brand_for_edit(call: CallbackQuery, state: FSMContext):
    brand_id = int(call.data.replace("edit_brand_", ""))
    try:
        brand = await sync_to_async(Brand.objects.get)(id=brand_id)
        await state.update_data(edit_brand_id=brand.id, edit_brand_name=brand.name)
        await state.set_state(BrandEditStates.waiting_for_new_data)

        await call.message.edit_text(
            f"✏️ <b>'{brand.name}' brendini tahrirlash</b>\n\n"
            f"Yangi nomini matn sifatida yuboring (yoki yangi <b>.svg</b> logotip faylini yuboring):",
            parse_mode="HTML"
        )
    except Exception as e:
        await call.message.edit_text(f"Xatolik: {e}")
    await call.answer()


@router.message(BrandEditStates.waiting_for_new_data, F.text)
async def process_edit_brand_name(message: Message, state: FSMContext):
    new_name = message.text.strip()
    if len(new_name) < 2:
        await message.answer("Nom kamida 2 ta harfdan iborat bo‘lishi kerak:")
        return

    data = await state.get_data()
    brand_id = data.get('edit_brand_id')

    try:
        brand = await sync_to_async(Brand.objects.get)(id=brand_id)
        old_name = brand.name
        brand.name = new_name
        from django.utils.text import slugify
        brand.slug = slugify(new_name)
        await sync_to_async(brand.save)()

        await state.clear()
        await message.answer(
            f"✅ <b>Brend nomi muvaffaqiyatli yangilandi!</b>\n\n"
            f"Eski: <i>{old_name}</i>\n"
            f"Yangi: <b>{new_name}</b>",
            reply_markup=get_section_crud_menu("Brend"),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"Xatolik: {e}")


@router.message(BrandEditStates.waiting_for_new_data, F.document | F.photo)
async def process_edit_brand_logo(message: Message, state: FSMContext, bot: Bot):
    if message.document:
        doc: Document = message.document
        ext = os.path.splitext(doc.file_name)[1].lower() if doc.file_name else '.svg'
        if not ext.endswith(('.svg', '.png', '.jpg', '.jpeg', '.webp')):
            await message.answer("Iltimos faqat .svg yoki rasm formatidagi logotip yuboring:")
            return
        file_obj = doc
    else:
        file_obj = message.photo[-1]
        ext = '.png'

    data = await state.get_data()
    brand_id = data.get('edit_brand_id')

    try:
        brand = await sync_to_async(Brand.objects.get)(id=brand_id)
        save_filename = f"{brand.slug}{ext}"
        dest_path = MEDIA_BRANDS_DIR / save_filename
        await bot.download(file_obj, destination=dest_path)

        brand.logo = f"brands/{save_filename}"
        await sync_to_async(brand.save)()

        await state.clear()
        import html
        await message.answer(
            f"✅ <b>'{html.escape(brand.name)}' logotipi yangilandi!</b>",
            reply_markup=get_section_crud_menu("Brend"),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"Xatolik: {e}")


@router.callback_query(F.data == "cancel_action")
async def cancel_inline(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Amal bekor qilindi.")
    await call.answer()

