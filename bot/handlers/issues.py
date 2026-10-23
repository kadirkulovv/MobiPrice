import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_section_crud_menu, get_cancel_menu
from bot.keyboards.common import build_3_row_reply_kb, build_3_row_inline_kb
from bot.states.admin_states import IssueAddStates, IssueEditStates
from bot.database import Brand, DeviceSeries, DevicePhone, DeviceIssue, sync_to_async
from bot.config import CHEATSHEET_IMG, ICONS_DIR
from bot.utils.translator import auto_translate_issue_title

router = Router()


@router.message(F.text == "🔧 Muammolar")
async def issues_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔧 <b>Muammolar va Detallar bo‘limi</b>\n\n"
        "Bu yerda har bir telefon uchun ta'mirlash turlari (Ekran, Batareya, Orqa shisha...) boshqariladi.\n"
        "<i>Har bir muammo 30 ta tayyor professional ikonkalardan biri bilan bog‘lanadi.</i>",
        reply_markup=get_section_crud_menu("Muammo"),
        parse_mode="HTML"
    )


@router.message(F.text == "📋 Muammo ro‘yxati")
async def list_issues(message: Message):
    issues = await sync_to_async(list)(
        DeviceIssue.objects.select_related('phone', 'phone__series', 'phone__series__brand').all().order_by('phone__name', 'title')[:30]
    )

    if not issues:
        await message.answer("Bazada hozircha muammolar/detallar kiritilmagan.")
        return

    text = "📋 <b>Mavjud Muammolar va Detallar:</b>\n\n"
    for idx, iss in enumerate(issues, 1):
        text += f"{idx}. <b>{iss.phone.name}</b> → {iss.title} (Ikonka: <b>#{iss.icon_number}</b>)\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "➕ Yangi Muammo qo‘shish")
async def add_issue_start(message: Message, state: FSMContext):
    brands = await sync_to_async(list)(Brand.objects.filter(is_active=True).order_by('name'))
    if not brands:
        await message.answer("Avval brend qo‘shishingiz kerak!")
        return

    brand_names = [b.name for b in brands]
    kb = build_3_row_reply_kb(brand_names, add_cancel=True)

    await state.set_state(IssueAddStates.waiting_for_brand)
    await message.answer(
        "1️⃣ <b>Ushbu muammo qaysi brend telefoniga tegishli?</b>\n"
        "Quyidagi brendlardan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(IssueAddStates.waiting_for_brand, F.text)
async def process_issue_brand(message: Message, state: FSMContext):
    brand_name = message.text.strip()
    try:
        brand = await sync_to_async(Brand.objects.get)(name__iexact=brand_name)
    except Brand.DoesNotExist:
        await message.answer("⚠️ Bunday brend topilmadi. Qaytadan tanlang:")
        return

    series_list = await sync_to_async(list)(DeviceSeries.objects.filter(brand=brand).order_by('name'))
    if not series_list:
        await message.answer(f"⚠️ '{brand.name}' brendida hali model seriyasi yo‘q!", reply_markup=get_section_crud_menu("Muammo"))
        await state.clear()
        return

    await state.update_data(brand_id=brand.id, brand_name=brand.name)
    await state.set_state(IssueAddStates.waiting_for_series)

    series_names = [s.name for s in series_list]
    kb = build_3_row_reply_kb(series_names, add_cancel=True)

    await message.answer(
        f"2️⃣ <b>Qaysi model seriyasiga ulanadi?</b>\n"
        f"Seriyalardan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(IssueAddStates.waiting_for_series, F.text)
async def process_issue_series(message: Message, state: FSMContext):
    series_name = message.text.strip()
    data = await state.get_data()
    brand_id = data.get('brand_id')

    try:
        series = await sync_to_async(DeviceSeries.objects.get)(brand_id=brand_id, name__iexact=series_name)
    except DeviceSeries.DoesNotExist:
        await message.answer("⚠️ Bunday seriya topilmadi. Qaytadan tanlang:")
        return

    phones_list = await sync_to_async(list)(DevicePhone.objects.filter(series=series).order_by('name'))
    if not phones_list:
        await message.answer(f"⚠️ '{series.name}' seriyasida hali telefon qo‘shilmagan! Avval '📱 Telefonlar' bo‘limidan telefon qo‘shing.", reply_markup=get_section_crud_menu("Muammo"))
        await state.clear()
        return

    await state.update_data(series_id=series.id, series_name=series.name)
    await state.set_state(IssueAddStates.waiting_for_phone)

    phone_names = [p.name for p in phones_list]
    kb = build_3_row_reply_kb(phone_names, add_cancel=True)

    await message.answer(
        f"3️⃣ <b>Qaysi telefonga ulanadi?</b>\n"
        f"Telefonlardan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(IssueAddStates.waiting_for_phone, F.text)
async def process_issue_phone(message: Message, state: FSMContext):
    phone_name = message.text.strip()
    data = await state.get_data()
    series_id = data.get('series_id')

    try:
        phone = await sync_to_async(DevicePhone.objects.get)(series_id=series_id, name__iexact=phone_name)
    except DevicePhone.DoesNotExist:
        await message.answer("⚠️ Bunday telefon topilmadi. Qaytadan tanlang:")
        return

    await state.update_data(phone_id=phone.id, phone_name=phone.name)
    await state.set_state(IssueAddStates.waiting_for_title)

    await message.answer(
        f"✅ Tanlandi: <b>{phone.name}</b>\n\n"
        f"4️⃣ <b>Muammo / Detal nomini kiriting:</b>\n"
        f"<i>(Masalan: Ekran (Displey), Orqa shisha (Lazer), Batareya, Kamera oynasi...)</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(IssueAddStates.waiting_for_title, F.text)
async def process_issue_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 2:
        await message.answer("Nom juda qisqa. Qaytadan kiriting:")
        return

    # Automatically translate to Russian and English in background
    title_ru, title_en = await auto_translate_issue_title(title)

    await state.update_data(
        issue_title=title,
        issue_title_ru=title_ru,
        issue_title_en=title_en,
    )
    await state.set_state(IssueAddStates.waiting_for_icon)

    # Send 30-icon cheatsheet image to the admin!
    caption = (
        f"📸 <b>30 ta tayyor ikonka katalogi</b>\n\n"
        f"🇺🇿 Detal nomi (UZ): <b>{title}</b>\n"
        f"🇷🇺 Ruscha (RU): <i>{title_ru}</i>\n"
        f"🇬🇧 Inglizcha (EN): <i>{title_en}</i>\n\n"
        f"5️⃣ Ushbu detal uchun rasmda ko‘rsatilgan mos ikonka raqamini yuboring:\n"
        f"<b>(1 dan 30 gacha raqam yozing)</b>"
    )

    if os.path.exists(CHEATSHEET_IMG):
        photo = FSInputFile(CHEATSHEET_IMG)
        await message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=get_cancel_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            caption,
            reply_markup=get_cancel_menu(),
            parse_mode="HTML"
        )


@router.message(IssueAddStates.waiting_for_icon, F.text)
async def process_issue_icon(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or not (1 <= int(text) <= 30):
        await message.answer("⚠️ Iltimos, 1 dan 30 gacha bo‘lgan son yuboring (masalan: 1, 4, 16):")
        return

    icon_num = int(text)
    data = await state.get_data()
    phone_id = data.get('phone_id')
    phone_name = data.get('phone_name')
    issue_title = data.get('issue_title')
    issue_title_ru = data.get('issue_title_ru', '')
    issue_title_en = data.get('issue_title_en', '')

    # Read SVG code from bot/assets/icons/{icon_num}.svg if present
    icon_svg_path = ICONS_DIR / f"{icon_num}.svg"
    svg_code = ""
    if os.path.exists(icon_svg_path):
        with open(icon_svg_path, 'r', encoding='utf-8') as f:
            svg_code = f.read()

    issue = await sync_to_async(DeviceIssue.objects.create)(
        phone_id=phone_id,
        title=issue_title,
        title_ru=issue_title_ru,
        title_en=issue_title_en,
        icon_number=icon_num,
        icon_svg=svg_code
    )

    await state.clear()
    await message.answer(
        f"🎉 <b>Yangi muammo / detal muvaffaqiyatli saqlandi!</b>\n\n"
        f"📱 Telefon: <b>{phone_name}</b>\n"
        f"🇺🇿 O‘zbekcha (UZ): <b>{issue.title}</b>\n"
        f"🇷🇺 Ruscha (RU): <i>{issue.title_ru}</i>\n"
        f"🇬🇧 Inglizcha (EN): <i>{issue.title_en}</i>\n"
        f"🔢 Ikonka: <b>#{icon_num}</b>",
        reply_markup=get_section_crud_menu("Muammo"),
        parse_mode="HTML"
    )


@router.message(F.text == "🗑 Muammo o‘chirish")
async def delete_issue_start(message: Message):
    issues = await sync_to_async(list)(DeviceIssue.objects.select_related('phone').all().order_by('-id')[:24])
    if not issues:
        await message.answer("O‘chirish uchun muammolar mavjud emas.")
        return

    items = [(f"{iss.phone.name} - {iss.title}", f"del_issue_{iss.id}") for iss in issues]
    kb = build_3_row_inline_kb(items, back_callback="", add_cancel=True)

    await message.answer(
        "🗑 <b>O‘chirmoqchi bo‘lgan muammoni tanlang:</b>\n"
        "<i>Eslatma: Muammo o‘chirilsa, uning narx va solishtirish kartalari ham o‘chadi!</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("del_issue_"))
async def process_delete_issue(call: CallbackQuery):
    issue_id = int(call.data.replace("del_issue_", ""))
    try:
        issue = await sync_to_async(DeviceIssue.objects.select_related('phone').get)(id=issue_id)
        name = f"{issue.phone.name} → {issue.title}"
        await sync_to_async(issue.delete)()
        await call.message.edit_text(f"✅ <b>{name}</b> muammosi muvaffaqiyatli o‘chirildi!", parse_mode="HTML")
    except Exception as e:
        await call.message.edit_text(f"Xatolik: {e}")
    await call.answer()


@router.message(F.text == "✏️ Muammo tahrirlash")
async def edit_issue_start(message: Message):
    issues = await sync_to_async(list)(DeviceIssue.objects.select_related('phone').all().order_by('-id')[:24])
    if not issues:
        await message.answer("Tahrirlash uchun muammolar mavjud emas.")
        return

    items = [(f"{iss.phone.name} - {iss.title}", f"edit_issue_{iss.id}") for iss in issues]
    kb = build_3_row_inline_kb(items, back_callback="", add_cancel=True)

    await message.answer(
        "✏️ <b>Tahrirlamoqchi bo‘lgan muammoni tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("edit_issue_"))
async def process_select_issue_for_edit(call: CallbackQuery, state: FSMContext):
    issue_id = int(call.data.replace("edit_issue_", ""))
    try:
        issue = await sync_to_async(DeviceIssue.objects.select_related('phone').get)(id=issue_id)
        await state.update_data(edit_issue_id=issue.id, edit_issue_title=issue.title)
        await state.set_state(IssueEditStates.waiting_for_new_data)

        await call.message.edit_text(
            f"✏️ <b>'{issue.phone.name} → {issue.title}' (Ikonka: #{issue.icon_number})</b>\n\n"
            f"Yangi nomini yozing (avtomatik tarjima qilinadi) <b>yoki</b> yangi ikonka raqamini yuboring (1-30):",
            parse_mode="HTML"
        )
    except Exception as e:
        await call.message.edit_text(f"Xatolik: {e}")
    await call.answer()


@router.message(IssueEditStates.waiting_for_new_data, F.text)
async def process_edit_issue_data(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    issue_id = data.get('edit_issue_id')

    try:
        issue = await sync_to_async(DeviceIssue.objects.get)(id=issue_id)

        # If user entered an icon number 1..30
        if text.isdigit() and (1 <= int(text) <= 30):
            icon_num = int(text)
            issue.icon_number = icon_num
            icon_svg_path = ICONS_DIR / f"{icon_num}.svg"
            if os.path.exists(icon_svg_path):
                with open(icon_svg_path, 'r', encoding='utf-8') as f:
                    issue.icon_svg = f.read()
            await sync_to_async(issue.save)()

            await state.clear()
            await message.answer(
                f"✅ <b>'{issue.title}' uchun ikonka #{icon_num} ga yangilandi!</b>",
                reply_markup=get_section_crud_menu("Muammo"),
                parse_mode="HTML"
            )
            return

        # Otherwise user entered new title -> auto-translate
        title_ru, title_en = await auto_translate_issue_title(text)
        old_title = issue.title
        issue.title = text
        issue.title_ru = title_ru
        issue.title_en = title_en
        await sync_to_async(issue.save)()

        await state.clear()
        await message.answer(
            f"✅ <b>Muammo nomi yangilandi va avtomatik tarjima qilindi!</b>\n\n"
            f"Eski: <i>{old_title}</i>\n"
            f"🇺🇿 UZ: <b>{issue.title}</b>\n"
            f"🇷🇺 RU: <i>{issue.title_ru}</i>\n"
            f"🇬🇧 EN: <i>{issue.title_en}</i>",
            reply_markup=get_section_crud_menu("Muammo"),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"Xatolik: {e}")

