import os
import html
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, PhotoSize, Document
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_section_crud_menu, get_cancel_menu
from bot.keyboards.common import build_3_row_reply_kb, build_3_row_inline_kb
from bot.states.admin_states import PhoneAddStates, PhoneEditStates
from bot.database import Brand, DeviceSeries, DevicePhone, make_safe_slug, sync_to_async
from bot.config import MEDIA_PHONES_DIR
from bot.handlers.start import require_site_admin

router = Router()


@router.message(F.text == "📱 Telefonlar")
async def phones_menu(message: Message, state: FSMContext):
    if not await require_site_admin(message):
        return
    await state.clear()
    await message.answer(
        "📱 <b>Telefonlar bo‘limi</b>\n\n"
        "Bu yerda aniq telefon modellari boshqariladi.\n"
        "<i>(Masalan: iPhone 16 Pro Max, iPhone 15 Pro, Galaxy S24 Ultra, Redmi Note 13 Pro va h.k.)</i>",
        reply_markup=get_section_crud_menu("Telefon"),
        parse_mode="HTML"
    )


@router.message(F.text == "📋 Telefon ro‘yxati")
async def list_phones(message: Message):
    if not await require_site_admin(message):
        return
    phones = await sync_to_async(list)(
        DevicePhone.objects.select_related('series', 'series__brand').all().order_by('series__brand__name', 'name')
    )

    if not phones:
        await message.answer("Bazada hozircha telefonlar qo‘shilmagan.")
        return

    text = "📋 <b>Mavjud Telefonlar ro‘yxati:</b>\n\n"
    current_brand = None
    for p in phones:
        brand_name = p.series.brand.name
        if brand_name != current_brand:
            current_brand = brand_name
            text += f"\n🏷 <b>{html.escape(current_brand)}:</b>\n"
        img_status = "🖼 Rasm bor" if p.image else "❌ Rasmsiz"
        text += f"  • <b>{html.escape(p.name)}</b> ({html.escape(p.series.name)}) — {img_status}\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "➕ Yangi Telefon qo‘shish")
async def add_phone_start(message: Message, state: FSMContext):
    if not await require_site_admin(message):
        return
    brands = await sync_to_async(list)(Brand.objects.filter(is_active=True).order_by('name'))
    if not brands:
        await message.answer("Avval brend qo‘shishingiz kerak!")
        return

    brand_names = [b.name for b in brands]
    kb = build_3_row_reply_kb(brand_names, add_cancel=True)

    await state.set_state(PhoneAddStates.waiting_for_brand)
    await message.answer(
        "1️⃣ <b>Telefon qaysi brendga tegishli?</b>\n"
        "Quyidagi brendlardan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(PhoneAddStates.waiting_for_brand, F.text)
async def process_phone_brand(message: Message, state: FSMContext):
    if not await require_site_admin(message):
        return
    brand_name = message.text.strip()
    try:
        brand = await sync_to_async(Brand.objects.get)(name__iexact=brand_name)
    except Brand.DoesNotExist:
        await message.answer("⚠️ Bunday brend topilmadi. Qaytadan tanlang:")
        return

    series_list = await sync_to_async(list)(DeviceSeries.objects.filter(brand=brand).order_by('name'))
    if not series_list:
        await message.answer(
            f"⚠️ '{brand.name}' brendi ostida hali model seriyasi yo‘q!\n"
            f"Avval '📂 Modellar' bo‘limidan seriya qo‘shing (masalan: Pro seriya, S seriya).",
            reply_markup=get_section_crud_menu("Telefon")
        )
        await state.clear()
        return

    await state.update_data(brand_id=brand.id, brand_name=brand.name)
    await state.set_state(PhoneAddStates.waiting_for_series)

    series_names = [s.name for s in series_list]
    kb = build_3_row_reply_kb(series_names, add_cancel=True)

    await message.answer(
        f"2️⃣ <b>'{html.escape(brand.name)}' brendining qaysi model seriyasiga ulanadi?</b>\n"
        f"Quyidagi seriyalardan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(PhoneAddStates.waiting_for_series, F.text)
async def process_phone_series(message: Message, state: FSMContext):
    if not await require_site_admin(message):
        return
    series_name = message.text.strip()
    data = await state.get_data()
    brand_id = data.get('brand_id')

    try:
        series = await sync_to_async(DeviceSeries.objects.get)(brand_id=brand_id, name__iexact=series_name)
    except DeviceSeries.DoesNotExist:
        await message.answer("⚠️ Bunday model seriyasi topilmadi. Qaytadan tanlang:")
        return

    await state.update_data(series_id=series.id, series_name=series.name)
    await state.set_state(PhoneAddStates.waiting_for_name)

    await message.answer(
        f"✅ Tanlandi: <b>{html.escape(data.get('brand_name', ''))} → {html.escape(series.name)}</b>\n\n"
        f"3️⃣ <b>Aniq telefon nomini kiriting:</b>\n"
        f"<i>(Masalan: iPhone 16 Pro Max, Galaxy S24 Ultra, Redmi Note 13 Pro...)</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(PhoneAddStates.waiting_for_name, F.text)
async def process_phone_name(message: Message, state: FSMContext):
    if not await require_site_admin(message):
        return
    phone_name = message.text.strip()
    if len(phone_name) < 2:
        await message.answer("Nom juda qisqa. Qaytadan kiriting:")
        return

    await state.update_data(phone_name=phone_name)
    await state.set_state(PhoneAddStates.waiting_for_image)

    await message.answer(
        f"✅ Telefon nomi: <b>{html.escape(phone_name)}</b>\n\n"
        f"4️⃣ <b>Telefon rasmini yuboring (JPG yoki PNG):</b>\n"
        f"<i>(Rasm yoki fotosurat sifatida yuborishingiz mumkin)</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


def _save_or_update_phone(series_id, phone_name, rel_image_path):
    phone = DevicePhone.objects.filter(series_id=series_id, name__iexact=phone_name).first()
    if not phone:
        phone = DevicePhone.objects.filter(name__iexact=phone_name).first()

    if phone:
        if series_id:
            phone.series_id = series_id
        phone.image = rel_image_path
        phone.save()
    else:
        phone = DevicePhone.objects.create(
            series_id=series_id,
            name=phone_name,
            image=rel_image_path
        )
    return DevicePhone.objects.select_related('series', 'series__brand').get(id=phone.id)


@router.message(PhoneAddStates.waiting_for_image, F.photo)
async def process_phone_image_photo(message: Message, state: FSMContext, bot: Bot):
    if not await require_site_admin(message):
        return
    try:
        photo: PhotoSize = message.photo[-1]
        data = await state.get_data()
        series_id = data.get('series_id')
        series_name = data.get('series_name', '')
        brand_name = data.get('brand_name', '')
        phone_name = data.get('phone_name', 'Telefon')

        file = await bot.get_file(photo.file_id)
        safe_slug = make_safe_slug(phone_name).replace('-', '_')
        save_filename = f"{safe_slug}.jpg"
        dest_path = MEDIA_PHONES_DIR / save_filename

        await bot.download_file(file.file_path, destination=dest_path)

        rel_path = f"phones/{save_filename}"
        phone = await sync_to_async(_save_or_update_phone)(series_id, phone_name, rel_path)

        display_series = phone.series.name if phone.series else series_name
        display_brand = phone.series.brand.name if (phone.series and phone.series.brand) else brand_name

        await state.clear()
        await message.answer(
            f"🎉 <b>Telefon rasmi muvaffaqiyatli saqlandi!</b>\n\n"
            f"📱 Nomi: <b>{html.escape(phone.name)}</b>\n"
            f"📂 Seriya: <b>{html.escape(display_series)}</b>\n"
            f"🏷 Brend: <b>{html.escape(display_brand)}</b>\n"
            f"🖼 Rasm fayli: <code>{html.escape(save_filename)}</code>",
            reply_markup=get_section_crud_menu("Telefon"),
            parse_mode="HTML"
        )
    except Exception as e:
        import logging
        logging.getLogger("mobiprice_bot").error(f"Error saving phone photo: {e}", exc_info=True)
        await message.answer(
            f"⚠️ Rasm saqlashda xatolik yuz berdi: {e}\n"
            f"Iltimos, qaytadan rasm yuboring yoki '❌ Bekor qilish' tugmasini bosing:",
            reply_markup=get_cancel_menu()
        )


@router.message(PhoneAddStates.waiting_for_image, F.document)
async def process_phone_image_doc(message: Message, state: FSMContext, bot: Bot):
    if not await require_site_admin(message):
        return
    try:
        doc: Document = message.document
        if not (doc.file_name or '').lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            await message.answer("⚠️ Iltimos faqat JPG, PNG yoki WEBP formatdagi rasm yuboring:")
            return

        data = await state.get_data()
        series_id = data.get('series_id')
        series_name = data.get('series_name', '')
        brand_name = data.get('brand_name', '')
        phone_name = data.get('phone_name', 'Telefon')

        file = await bot.get_file(doc.file_id)
        ext = os.path.splitext(doc.file_name)[1].lower() or '.jpg'
        safe_slug = make_safe_slug(phone_name).replace('-', '_')
        save_filename = f"{safe_slug}{ext}"
        dest_path = MEDIA_PHONES_DIR / save_filename

        await bot.download_file(file.file_path, destination=dest_path)

        rel_path = f"phones/{save_filename}"
        phone = await sync_to_async(_save_or_update_phone)(series_id, phone_name, rel_path)

        display_series = phone.series.name if phone.series else series_name
        display_brand = phone.series.brand.name if (phone.series and phone.series.brand) else brand_name

        await state.clear()
        await message.answer(
            f"🎉 <b>Telefon rasmi muvaffaqiyatli saqlandi!</b>\n\n"
            f"📱 Nomi: <b>{html.escape(phone.name)}</b>\n"
            f"📂 Seriya: <b>{html.escape(display_series)}</b>\n"
            f"🏷 Brend: <b>{html.escape(display_brand)}</b>\n"
            f"🖼 Rasm fayli: <code>{html.escape(save_filename)}</code>",
            reply_markup=get_section_crud_menu("Telefon"),
            parse_mode="HTML"
        )
    except Exception as e:
        import logging
        logging.getLogger("mobiprice_bot").error(f"Error saving phone doc: {e}", exc_info=True)
        await message.answer(
            f"⚠️ Faylni saqlashda xatolik yuz berdi: {e}\n"
            f"Iltimos, qaytadan rasm yuboring:",
            reply_markup=get_cancel_menu()
        )


@router.message(PhoneAddStates.waiting_for_image)
async def process_phone_image_invalid(message: Message):
    if not await require_site_admin(message):
        return
    await message.answer(
        "⚠️ Iltimos, telefon rasmini fotosurat yoki fayl (JPG/PNG) sifatida yuboring:\n"
        "(Yoki '❌ Bekor qilish' tugmasini bosing)",
        reply_markup=get_cancel_menu()
    )


@router.message(F.text == "🗑 Telefon o‘chirish")
async def delete_phone_start(message: Message):
    if not await require_site_admin(message):
        return
    phones = await sync_to_async(list)(DevicePhone.objects.select_related('series', 'series__brand').all().order_by('name'))
    if not phones:
        await message.answer("O‘chirish uchun telefonlar mavjud emas.")
        return

    items = [(f"{p.name}", f"del_phone_{p.id}") for p in phones[:24]]
    kb = build_3_row_inline_kb(items, back_callback="", add_cancel=True)

    await message.answer(
        "🗑 <b>O‘chirmoqchi bo‘lgan telefoningizni tanlang:</b>\n"
        "<i>Eslatma: Telefon o‘chirilsa, uning barcha muammolari va narxlari ham o‘chadi!</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("del_phone_"))
async def process_delete_phone(call: CallbackQuery):
    if not await require_site_admin(call):
        return
    phone_id = int(call.data.replace("del_phone_", ""))
    try:
        phone = await sync_to_async(DevicePhone.objects.select_related('series', 'series__brand').get)(id=phone_id)
        name = phone.name
        await sync_to_async(phone.delete)()
        await call.message.edit_text(f"✅ <b>{html.escape(name)}</b> telefoni muvaffaqiyatli o‘chirildi!", parse_mode="HTML")
    except Exception as e:
        await call.message.edit_text(f"Xatolik: {e}")
    await call.answer()


@router.message(F.text == "✏️ Telefon tahrirlash")
async def edit_phone_start(message: Message):
    if not await require_site_admin(message):
        return
    phones = await sync_to_async(list)(DevicePhone.objects.select_related('series', 'series__brand').all().order_by('name'))
    if not phones:
        await message.answer("Tahrirlash uchun telefonlar mavjud emas.")
        return

    items = [(f"{p.name}", f"edit_phone_{p.id}") for p in phones[:24]]
    kb = build_3_row_inline_kb(items, back_callback="", add_cancel=True)

    await message.answer(
        "✏️ <b>Tahrirlamoqchi bo‘lgan telefonni tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("edit_phone_"))
async def process_select_phone_for_edit(call: CallbackQuery, state: FSMContext):
    if not await require_site_admin(call):
        return
    phone_id = int(call.data.replace("edit_phone_", ""))
    try:
        phone = await sync_to_async(DevicePhone.objects.select_related('series', 'series__brand').get)(id=phone_id)
        await state.update_data(edit_phone_id=phone.id, edit_phone_name=phone.name)
        await state.set_state(PhoneEditStates.waiting_for_new_data)

        await call.message.edit_text(
            f"✏️ <b>'{html.escape(phone.name)}' telefonini tahrirlash</b>\n\n"
            f"Yangi nomini matn sifatida yozing (yoki yangi rasmini JPG/PNG sifatida yuboring):",
            parse_mode="HTML"
        )
    except Exception as e:
        await call.message.edit_text(f"Xatolik: {e}")
    await call.answer()


@router.message(PhoneEditStates.waiting_for_new_data, F.text)
async def process_edit_phone_name(message: Message, state: FSMContext):
    if not await require_site_admin(message):
        return
    new_name = message.text.strip()
    if len(new_name) < 2:
        await message.answer("Nom juda qisqa. Qaytadan kiriting:")
        return

    data = await state.get_data()
    phone_id = data.get('edit_phone_id')

    try:
        phone = await sync_to_async(DevicePhone.objects.get)(id=phone_id)
        old_name = phone.name
        phone.name = new_name
        phone.slug = ""
        await sync_to_async(phone.save)()

        await state.clear()
        await message.answer(
            f"✅ <b>Telefon nomi yangilandi!</b>\n\n"
            f"Eski: <i>{html.escape(old_name)}</i>\n"
            f"Yangi: <b>{html.escape(new_name)}</b>",
            reply_markup=get_section_crud_menu("Telefon"),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"Xatolik: {e}")


@router.message(PhoneEditStates.waiting_for_new_data, F.photo)
async def process_edit_phone_photo(message: Message, state: FSMContext, bot: Bot):
    if not await require_site_admin(message):
        return
    photo: PhotoSize = message.photo[-1]
    data = await state.get_data()
    phone_id = data.get('edit_phone_id')

    try:
        phone = await sync_to_async(DevicePhone.objects.get)(id=phone_id)
        file = await bot.get_file(photo.file_id)
        save_filename = f"{phone.slug}.jpg"
        dest_path = MEDIA_PHONES_DIR / save_filename
        await bot.download_file(file.file_path, destination=dest_path)

        phone.image = f"phones/{save_filename}"
        await sync_to_async(phone.save)()

        await state.clear()
        await message.answer(
            f"✅ <b>'{html.escape(phone.name)}' rasmi muvaffaqiyatli yangilandi!</b>",
            reply_markup=get_section_crud_menu("Telefon"),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"Xatolik: {e}")


@router.message(PhoneEditStates.waiting_for_new_data, F.document)
async def process_edit_phone_doc(message: Message, state: FSMContext, bot: Bot):
    if not await require_site_admin(message):
        return
    doc: Document = message.document
    if not (doc.file_name or '').lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        await message.answer("⚠️ Iltimos faqat JPG yoki PNG formatdagi rasm yuboring:")
        return

    data = await state.get_data()
    phone_id = data.get('edit_phone_id')

    try:
        phone = await sync_to_async(DevicePhone.objects.get)(id=phone_id)
        file = await bot.get_file(doc.file_id)
        ext = os.path.splitext(doc.file_name)[1].lower() or '.jpg'
        save_filename = f"{phone.slug}{ext}"
        dest_path = MEDIA_PHONES_DIR / save_filename
        await bot.download_file(file.file_path, destination=dest_path)

        phone.image = f"phones/{save_filename}"
        await sync_to_async(phone.save)()

        await state.clear()
        await message.answer(
            f"✅ <b>'{html.escape(phone.name)}' rasmi muvaffaqiyatli yangilandi!</b>",
            reply_markup=get_section_crud_menu("Telefon"),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"Xatolik: {e}")


