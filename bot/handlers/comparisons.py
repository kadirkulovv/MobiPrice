from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_section_crud_menu, get_cancel_menu
from bot.keyboards.common import build_3_row_reply_kb, build_3_row_inline_kb
from bot.states.admin_states import ComparisonAddStates, ComparisonEditStates
from bot.database import Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison, sync_to_async

router = Router()


@router.message(F.text == "⚖️ Solishtirish (Narxlar)")
async def comparisons_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "⚖️ <b>Solishtirish va Narxlar bo‘limi</b>\n\n"
        "Bu yerda har bir muammo uchun faqat <b>Original</b> yoki <b>Kopiya</b> narxi va <b>ombordagi soni</b> kiritiladi.\n"
        "Ortiqcha kafolat so‘ralmaydi, narx va mavjudlik darhol saytda aks etadi.",
        reply_markup=get_section_crud_menu("Narx"),
        parse_mode="HTML"
    )


@router.message(F.text == "📋 Narx ro‘yxati")
async def list_comparisons(message: Message):
    comp_list = await sync_to_async(list)(
        IssueComparison.objects.select_related('issue', 'issue__phone', 'issue__phone__series__brand').all().order_by('-id')[:25]
    )

    if not comp_list:
        await message.answer("Bazada hozircha narxlar kiritilmagan.")
        return

    text = "📋 <b>Mavjud narxlar va qoldiq ro‘yxati:</b>\n\n"
    for idx, c in enumerate(comp_list, 1):
        phone_name = c.issue.phone.name
        issue_title = c.issue.title
        total = f"{c.part_price_uzs:,} so'm"
        stock = f"✅ {c.quantity} ta" if (c.is_in_stock and c.quantity > 0) else "❌ Tugagan"
        text += f"{idx}. <b>{phone_name}</b> → {issue_title}\n"
        text += f"   🏷 {c.title} — <b>{total}</b> ({stock})\n"

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

    quality_options = ["🌟 Original Zavod", "⚡️ Sifatli Kopiya"]
    kb = build_3_row_reply_kb(quality_options, add_cancel=True)

    await message.answer(
        f"✅ Tanlandi: <b>{data.get('phone_name')} → {issue.title}</b>\n\n"
        f"5️⃣ <b>Variant turini tanlang (Original yoki Kopiya):</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_quality, F.text)
async def process_comp_quality(message: Message, state: FSMContext):
    choice = message.text.strip()
    is_original = "original" in choice.lower()

    if is_original:
        quality_type = "original_service_pack"
        title_uz = "Original Zavod"
        title_ru = "Оригинал Завод"
        title_en = "Original Factory"
        badge = "Original"
    else:
        quality_type = "tft_incell"
        title_uz = "Sifatli Kopiya"
        title_ru = "Качественная Копия"
        title_en = "High-Quality Copy"
        badge = "Kopiya"

    await state.update_data(
        quality_type=quality_type,
        title_uz=title_uz,
        title_ru=title_ru,
        title_en=title_en,
        badge=badge,
    )
    await state.set_state(ComparisonAddStates.waiting_for_price)

    await message.answer(
        f"✅ Tanlandi: <b>{title_uz}</b>\n\n"
        f"6️⃣ <b>Ushbu variant narxini kiriting (so‘mda, faqat raqam):</b>\n"
        f"<i>(Masalan: 1200000 yoki 450000)</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_price, F.text)
async def process_comp_price(message: Message, state: FSMContext):
    val = message.text.replace(' ', '').replace(',', '').strip()
    if not val.isdigit():
        await message.answer("⚠️ Iltimos faqat raqam kiriting (masalan: 1200000):")
        return

    price = int(val)
    if price <= 0:
        await message.answer("Narx 0 dan katta bo‘lishi kerak. Qaytadan kiriting:")
        return

    price_usd = max(1, price // 12800)
    await state.update_data(part_price_uzs=price, price_usd=price_usd)
    await state.set_state(ComparisonAddStates.waiting_for_quantity)

    await message.answer(
        f"✅ Narx: <b>{price:,} so‘m</b>\n\n"
        f"7️⃣ <b>Ombordagi soni (miqdori) nechta?</b>\n"
        f"<i>(Masalan: 5 yoki 10. Hozirda omborda bo‘lmasa 0 deb yozing)</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(ComparisonAddStates.waiting_for_quantity, F.text)
async def process_comp_quantity(message: Message, state: FSMContext):
    val = message.text.strip()
    if not val.isdigit():
        await message.answer("⚠️ Iltimos faqat son kiriting (masalan: 5 yoki 0):")
        return

    qty = int(val)
    is_in_stock = (qty > 0)

    data = await state.get_data()
    issue_id = data.get('issue_id')
    issue_title = data.get('issue_title')
    phone_name = data.get('phone_name')
    quality_type = data.get('quality_type')
    title_uz = data.get('title_uz')
    title_ru = data.get('title_ru')
    title_en = data.get('title_en')
    badge = data.get('badge')
    price = data.get('part_price_uzs')
    price_usd = data.get('price_usd')

    # Save comparison
    comparison = await sync_to_async(IssueComparison.objects.create)(
        issue_id=issue_id,
        quality_type=quality_type,
        title=title_uz,
        title_ru=title_ru,
        title_en=title_en,
        part_price_uzs=price,
        service_fee_uzs=0,
        price_usd=price_usd,
        quantity=qty,
        is_in_stock=is_in_stock,
        warranty="Kafolat mavjud",
        warranty_ru="С гарантией",
        warranty_en="With warranty",
        repair_time="30 daqiqa",
        badge=badge,
        description=""
    )

    stock_text = f"✅ Mavjud (Omborda: {qty} ta)" if is_in_stock else "❌ Tugagan (Mavjud emas)"

    await state.clear()
    await message.answer(
        f"🎉 <b>Narx va miqdor muvaffaqiyatli saqlandi!</b>\n\n"
        f"📱 Telefon: <b>{phone_name}</b>\n"
        f"🔧 Muammo: <b>{issue_title}</b>\n"
        f"🏷 Turi: <b>{comparison.title}</b> ({comparison.badge})\n"
        f"💵 Narxi: <b>{price:,} so‘m</b> (~${price_usd} USD)\n"
        f"📦 Qoldiq: <b>{stock_text}</b>",
        reply_markup=get_section_crud_menu("Narx"),
        parse_mode="HTML"
    )


# --- EDIT (UPDATE) ---

@router.message(F.text == "✏️ Narx tahrirlash")
async def edit_comparison_start(message: Message):
    comp_list = await sync_to_async(list)(
        IssueComparison.objects.select_related('issue', 'issue__phone').all().order_by('-id')[:24]
    )
    if not comp_list:
        await message.answer("Tahrirlash uchun narxlar mavjud emas.")
        return

    items = [(f"{c.issue.phone.name} {c.issue.title} ({c.badge})", f"edit_comp_{c.id}") for c in comp_list]
    kb = build_3_row_inline_kb(items, back_callback="", add_cancel=True)

    await message.answer(
        "✏️ <b>Tahrirlamoqchi bo‘lgan narx variantini tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("edit_comp_"))
async def process_select_comp_for_edit(call: CallbackQuery, state: FSMContext):
    comp_id = int(call.data.replace("edit_comp_", ""))
    try:
        comp = await sync_to_async(IssueComparison.objects.select_related('issue', 'issue__phone').get)(id=comp_id)
        await state.update_data(edit_comp_id=comp.id)
        await state.set_state(ComparisonEditStates.waiting_for_new_price)

        stock_str = f"{comp.quantity} ta" if comp.is_in_stock else "Tugagan"

        await call.message.edit_text(
            f"✏️ <b>{comp.issue.phone.name} → {comp.issue.title} ({comp.title})</b>\n\n"
            f"Hozirgi narxi: <b>{comp.part_price_uzs:,} so‘m</b>\n"
            f"Ombordagi qoldiq: <b>{stock_str}</b>\n\n"
            f"1️⃣ Yangi narxini kiriting (so‘mda, o‘zgarmasa avvalgisini yozing):",
            parse_mode="HTML"
        )
    except Exception as e:
        await call.message.edit_text(f"Xatolik: {e}")
    await call.answer()


@router.message(ComparisonEditStates.waiting_for_new_price, F.text)
async def process_edit_comp_price(message: Message, state: FSMContext):
    val = message.text.replace(' ', '').replace(',', '').strip()
    if not val.isdigit():
        await message.answer("⚠️ Iltimos faqat raqam kiriting (masalan: 1200000):")
        return

    new_price = int(val)
    await state.update_data(edit_new_price=new_price)
    await state.set_state(ComparisonEditStates.waiting_for_new_qty)

    await message.answer(
        f"✅ Yangi narx: <b>{new_price:,} so‘m</b>\n\n"
        f"2️⃣ Endi ombordagi yangi sonini kiriting (masalan: 5 yoki 0):",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(ComparisonEditStates.waiting_for_new_qty, F.text)
async def process_edit_comp_qty(message: Message, state: FSMContext):
    val = message.text.strip()
    if not val.isdigit():
        await message.answer("⚠️ Iltimos faqat son kiriting (masalan: 5 yoki 0):")
        return

    new_qty = int(val)
    data = await state.get_data()
    comp_id = data.get('edit_comp_id')
    new_price = data.get('edit_new_price')

    try:
        comp = await sync_to_async(IssueComparison.objects.get)(id=comp_id)
        comp.part_price_uzs = new_price
        comp.price_usd = max(1, new_price // 12800)
        comp.quantity = new_qty
        comp.is_in_stock = (new_qty > 0)
        await sync_to_async(comp.save)()

        stock_text = f"✅ Mavjud ({new_qty} ta)" if comp.is_in_stock else "❌ Tugagan (Mavjud emas)"

        await state.clear()
        await message.answer(
            f"✅ <b>Narx va miqdor muvaffaqiyatli yangilandi!</b>\n\n"
            f"🏷 {comp.title}\n"
            f"💵 Yangi narxi: <b>{new_price:,} so‘m</b>\n"
            f"📦 Qoldiq: <b>{stock_text}</b>",
            reply_markup=get_section_crud_menu("Narx"),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"Xatolik: {e}")


# --- DELETE ---

@router.message(F.text == "🗑 Narx o‘chirish")
async def delete_comparison_start(message: Message):
    comp_list = await sync_to_async(list)(
        IssueComparison.objects.select_related('issue', 'issue__phone').all().order_by('-id')[:24]
    )
    if not comp_list:
        await message.answer("O‘chirish uchun narxlar mavjud emas.")
        return

    items = [(f"{c.issue.phone.name} {c.issue.title} ({c.badge})", f"del_comp_{c.id}") for c in comp_list]
    kb = build_3_row_inline_kb(items, back_callback="", add_cancel=True)

    await message.answer(
        "🗑 <b>O‘chirmoqchi bo‘lgan narx variantini tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("del_comp_"))
async def process_delete_comparison(call: CallbackQuery):
    comp_id = int(call.data.replace("del_comp_", ""))
    try:
        comp = await sync_to_async(IssueComparison.objects.get)(id=comp_id)
        name = f"{comp.issue.phone.name} → {comp.issue.title} ({comp.title})"
        await sync_to_async(comp.delete)()
        await call.message.edit_text(f"✅ <b>{name}</b> narxi muvaffaqiyatli o‘chirildi!", parse_mode="HTML")
    except Exception as e:
        await call.message.edit_text(f"Xatolik: {e}")
    await call.answer()
