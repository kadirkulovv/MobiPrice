from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_section_crud_menu, get_cancel_menu
from bot.keyboards.common import build_3_row_reply_kb, build_3_row_inline_kb
from bot.states.admin_states import ComparisonAddStates
from bot.database import Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison, sync_to_async

router = Router()

QUALITY_MAP = {
    "Original Zavod": "original_service_pack",
    "OLED GX Kopiya": "oled_gx",
    "Incell / TFT Byudjet": "tft_incell",
    "Original Donar": "original_donor",
}


@router.message(F.text == "⚖️ Solishtirish (Narxlar)")
async def comparisons_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "⚖️ <b>Solishtirish va Narxlar bo‘limi</b>\n\n"
        "Bu yerda har bir muammo uchun narx variantlari (Original Zavod vs Kopiya) kiritiladi.\n"
        "Mijoz saytda taqqoslash imkoniyatiga ega bo‘ladi.",
        reply_markup=get_section_crud_menu("Narx"),
        parse_mode="HTML"
    )


@router.message(F.text == "📋 Narx ro‘yxati")
async def list_comparisons(message: Message):
    comp_list = await sync_to_async(list)(
        IssueComparison.objects.select_related('issue', 'issue__phone', 'issue__phone__series__brand').all().order_by('-id')[:20]
    )

    if not comp_list:
        await message.answer("Bazada hozircha narxlar/solishtirish variantlari kiritilmagan.")
        return

    text = "📋 <b>Oxirgi kiritilgan narxlar ro‘yxati:</b>\n\n"
    for idx, c in enumerate(comp_list, 1):
        phone_name = c.issue.phone.name
        issue_title = c.issue.title
        total = f"{c.total_price_uzs:,} so'm"
        text += f"{idx}. <b>{phone_name}</b> → {issue_title}\n"
        text += f"   🏷 {c.title} — <b>{total}</b> (🛡 {c.warranty})\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "➕ Yangi Narx qo‘shish")
async def add_comparison_start(message: Message, state: FSMContext):
    brands = await sync_to_async(list)(Brand.objects.filter(is_active=True).order_by('name'))
    if not brands:
        await message.answer("Avval brend qo‘shishingiz kerak!")
        return

    brand_names = [b.name for b in brands]
    kb = build_3_row_reply_kb(brand_names, add_cancel=True)

    await state.set_state(ComparisonAddStates.waiting_for_brand)
    await message.answer(
        "1️⃣ <b>1-Qadam: Brendni tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_brand, F.text)
async def process_comp_brand(message: Message, state: FSMContext):
    brand_name = message.text.strip()
    try:
        brand = await sync_to_async(Brand.objects.get)(name__iexact=brand_name)
    except Brand.DoesNotExist:
        await message.answer("⚠️ Bunday brend topilmadi. Qaytadan tanlang:")
        return

    series_list = await sync_to_async(list)(DeviceSeries.objects.filter(brand=brand).order_by('name'))
    if not series_list:
        await message.answer(f"⚠️ '{brand.name}' brendida hali model seriyasi yo‘q!", reply_markup=get_section_crud_menu("Narx"))
        await state.clear()
        return

    await state.update_data(brand_id=brand.id, brand_name=brand.name)
    await state.set_state(ComparisonAddStates.waiting_for_series)

    series_names = [s.name for s in series_list]
    kb = build_3_row_reply_kb(series_names, add_cancel=True)

    await message.answer(
        f"2️⃣ <b>2-Qadam: Model seriyasini tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_series, F.text)
async def process_comp_series(message: Message, state: FSMContext):
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
        await message.answer(f"⚠️ '{series.name}' seriyasida hali telefon qo‘shilmagan!", reply_markup=get_section_crud_menu("Narx"))
        await state.clear()
        return

    await state.update_data(series_id=series.id, series_name=series.name)
    await state.set_state(ComparisonAddStates.waiting_for_phone)

    phone_names = [p.name for p in phones_list]
    kb = build_3_row_reply_kb(phone_names, add_cancel=True)

    await message.answer(
        f"3️⃣ <b>3-Qadam: Telefonni tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_phone, F.text)
async def process_comp_phone(message: Message, state: FSMContext):
    phone_name = message.text.strip()
    data = await state.get_data()
    series_id = data.get('series_id')

    try:
        phone = await sync_to_async(DevicePhone.objects.get)(series_id=series_id, name__iexact=phone_name)
    except DevicePhone.DoesNotExist:
        await message.answer("⚠️ Bunday telefon topilmadi. Qaytadan tanlang:")
        return

    issues_list = await sync_to_async(list)(DeviceIssue.objects.filter(phone=phone).order_by('title'))
    if not issues_list:
        await message.answer(
            f"⚠️ '{phone.name}' telefonida hali muammo/detallar qo‘shilmagan!\n"
            f"Avval '🔧 Muammolar' bo‘limidan detal qo‘shing.",
            reply_markup=get_section_crud_menu("Narx")
        )
        await state.clear()
        return

    await state.update_data(phone_id=phone.id, phone_name=phone.name)
    await state.set_state(ComparisonAddStates.waiting_for_issue)

    issue_names = [iss.title for iss in issues_list]
    kb = build_3_row_reply_kb(issue_names, add_cancel=True)

    await message.answer(
        f"4️⃣ <b>4-Qadam: Muammoni / Detalni tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_issue, F.text)
async def process_comp_issue(message: Message, state: FSMContext):
    issue_title = message.text.strip()
    data = await state.get_data()
    phone_id = data.get('phone_id')

    try:
        issue = await sync_to_async(DeviceIssue.objects.get)(phone_id=phone_id, title__iexact=issue_title)
    except DeviceIssue.DoesNotExist:
        await message.answer("⚠️ Bunday muammo topilmadi. Qaytadan tanlang:")
        return

    await state.update_data(issue_id=issue.id, issue_title=issue.title)
    await state.set_state(ComparisonAddStates.waiting_for_quality)

    quality_options = ["Original Zavod", "OLED GX Kopiya", "Incell / TFT Byudjet"]
    kb = build_3_row_reply_kb(quality_options, add_cancel=True)

    await message.answer(
        f"✅ Tanlandi: <b>{data.get('phone_name')} → {issue.title}</b>\n\n"
        f"5️⃣ <b>Sifat toifasini tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_quality, F.text)
async def process_comp_quality(message: Message, state: FSMContext):
    choice = message.text.strip()
    quality_key = QUALITY_MAP.get(choice, "original_service_pack")

    await state.update_data(quality_type=quality_key, quality_choice=choice)
    await state.set_state(ComparisonAddStates.waiting_for_title)

    default_title = "Original Zavod Service Pack (100% Original)" if "Original" in choice else choice
    await message.answer(
        f"6️⃣ <b>Variant sarlavhasini kiriting:</b>\n"
        f"<i>(Masalan: {default_title})</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_title, F.text)
async def process_comp_title(message: Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    await state.set_state(ComparisonAddStates.waiting_for_part_price)

    await message.answer(
        f"7️⃣ <b>Zapchast narxini kiriting (so‘mda, faqat raqam):</b>\n"
        f"<i>(Masalan: 2500000)</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_part_price, F.text)
async def process_comp_part_price(message: Message, state: FSMContext):
    val = message.text.replace(' ', '').replace(',', '').strip()
    if not val.isdigit():
        await message.answer("⚠️ Iltimos faqat raqam kiriting (masalan: 1800000):")
        return

    part_price = int(val)
    await state.update_data(part_price_uzs=part_price)
    await state.set_state(ComparisonAddStates.waiting_for_service_fee)

    await message.answer(
        f"8️⃣ <b>Usta haqqini kiriting (so‘mda, faqat raqam):</b>\n"
        f"<i>(Masalan: 150000 yoki bepul bo‘lsa 0)</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_service_fee, F.text)
async def process_comp_service_fee(message: Message, state: FSMContext):
    val = message.text.replace(' ', '').replace(',', '').strip()
    if not val.isdigit():
        await message.answer("⚠️ Iltimos faqat raqam kiriting (masalan: 150000):")
        return

    service_fee = int(val)
    await state.update_data(service_fee_uzs=service_fee)
    await state.set_state(ComparisonAddStates.waiting_for_warranty)

    kb = build_3_row_reply_kb(["6 oy kafolat", "3 oy kafolat", "1 oy kafolat"], add_cancel=True)
    await message.answer(
        f"9️⃣ <b>Kafolat muddatini tanlang yoki yozing:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_warranty, F.text)
async def process_comp_warranty(message: Message, state: FSMContext):
    warranty = message.text.strip()
    await state.update_data(warranty=warranty)
    await state.set_state(ComparisonAddStates.waiting_for_repair_time)

    kb = build_3_row_reply_kb(["30 daqiqa", "45 daqiqa", "1 soat"], add_cancel=True)
    await message.answer(
        f"🔟 <b>Ta'mirlash vaqtini tanlang yoki yozing:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_repair_time, F.text)
async def process_comp_repair_time(message: Message, state: FSMContext):
    repair_time = message.text.strip()
    await state.update_data(repair_time=repair_time)
    await state.set_state(ComparisonAddStates.waiting_for_desc)

    await message.answer(
        f"1️⃣1️⃣ <b>Qisqa tavsif / Farqi nimada?</b>\n"
        f"<i>(Masalan: 100% Zavodskoy yangi original displey. TrueTone datchigi to‘liq o‘tadi, 120Hz ProMotion ravon ishlaydi.)</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_desc, F.text)
async def process_comp_desc(message: Message, state: FSMContext):
    desc = message.text.strip()
    data = await state.get_data()

    issue_id = data.get('issue_id')
    quality_type = data.get('quality_type')
    title = data.get('title')
    part_price = data.get('part_price_uzs')
    service_fee = data.get('service_fee_uzs')
    warranty = data.get('warranty')
    repair_time = data.get('repair_time')
    phone_name = data.get('phone_name')
    issue_title = data.get('issue_title')

    badge = "Tavsiya etiladi" if quality_type == 'original_service_pack' else ("Optimal narx" if quality_type == 'oled_gx' else "Hamyonbop")
    usd_approx = int(round((part_price + service_fee) / 12800))

    comp = await sync_to_async(IssueComparison.objects.create)(
        issue_id=issue_id,
        quality_type=quality_type,
        title=title,
        part_price_uzs=part_price,
        service_fee_uzs=service_fee,
        price_usd=usd_approx,
        warranty=warranty,
        repair_time=repair_time,
        badge=badge,
        description=desc,
    )

    total_str = f"{comp.total_price_uzs:,} so'm"

    await state.clear()
    await message.answer(
        f"🎉 <b>Yangi narx varianti muvaffaqiyatli saqlandi!</b>\n\n"
        f"📱 Telefon: <b>{phone_name}</b>\n"
        f"🔧 Muammo: <b>{issue_title}</b>\n"
        f"🏷 Variant: <b>{title}</b>\n"
        f"💵 Umumiy narx: <b>{total_str}</b> (~${usd_approx})\n"
        f"🛡 Kafolat: <b>{warranty}</b>\n"
        f"⏱ Vaqt: <b>{repair_time}</b>",
        reply_markup=get_section_crud_menu("Narx"),
        parse_mode="HTML"
    )


@router.message(F.text == "🗑 Narx o‘chirish")
async def delete_comp_start(message: Message):
    comp_list = await sync_to_async(list)(
        IssueComparison.objects.select_related('issue', 'issue__phone').all().order_by('-id')[:24]
    )
    if not comp_list:
        await message.answer("O‘chirish uchun narxlar mavjud emas.")
        return

    items = [(f"{c.issue.phone.name}: {c.title[:18]}", f"del_comp_{c.id}") for c in comp_list]
    kb = build_3_row_inline_kb(items, back_callback="", add_cancel=True)

    await message.answer(
        "🗑 <b>O‘chirmoqchi bo‘lgan narx variantini tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("del_comp_"))
async def process_delete_comp(call: CallbackQuery):
    comp_id = int(call.data.replace("del_comp_", ""))
    try:
        comp = await sync_to_async(IssueComparison.objects.get)(id=comp_id)
        name = f"{comp.issue.phone.name} → {comp.title}"
        await sync_to_async(comp.delete)()
        await call.message.edit_text(f"✅ <b>{name}</b> narxi muvaffaqiyatli o‘chirildi!", parse_mode="HTML")
    except Exception as e:
        await call.message.edit_text(f"Xatolik: {e}")
    await call.answer()
