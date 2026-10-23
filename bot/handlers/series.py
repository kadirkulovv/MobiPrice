from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_section_crud_menu, get_cancel_menu
from bot.keyboards.common import build_3_row_reply_kb, build_3_row_inline_kb
from bot.states.admin_states import SeriesAddStates, SeriesEditStates
from bot.database import Brand, DeviceSeries, sync_to_async

router = Router()


@router.message(F.text == "📂 Modellar")
async def series_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📂 <b>Model seriyalari bo‘limi</b>\n\n"
        "Bu yerda har bir brend ostidagi model seriyalari boshqariladi.\n"
        "<i>(Masalan: Apple uchun Pro seriya, Pro Max seriya; Samsung uchun S seriya, A seriya va h.k.)</i>",
        reply_markup=get_section_crud_menu("Model"),
        parse_mode="HTML"
    )


@router.message(F.text == "📋 Model ro‘yxati")
async def list_series(message: Message):
    series_list = await sync_to_async(list)(
        DeviceSeries.objects.select_related('brand').all().order_by('brand__name', 'name')
    )

    if not series_list:
        await message.answer("Bazada hozircha model seriyalari qo‘shilmagan.")
        return

    text = "📋 <b>Mavjud Model seriyalari:</b>\n\n"
    current_brand = None
    for s in series_list:
        if s.brand.name != current_brand:
            current_brand = s.brand.name
            text += f"\n🏷 <b>{current_brand}:</b>\n"
        text += f"  • {s.name} (id: <code>{s.id}</code>)\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "➕ Yangi Model qo‘shish")
async def add_series_start(message: Message, state: FSMContext):
    brands = await sync_to_async(list)(Brand.objects.filter(is_active=True).order_by('name'))
    if not brands:
        await message.answer("Avval brend qo‘shishingiz kerak! Hozircha bazada brendlar yo‘q.")
        return

    brand_names = [b.name for b in brands]
    kb = build_3_row_reply_kb(brand_names, add_cancel=True)

    await state.set_state(SeriesAddStates.waiting_for_brand)
    await message.answer(
        "👇 <b>Ushbu model seriyasi qaysi brendga ulanadi?</b>\n"
        "Quyidagi brendlardan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(SeriesAddStates.waiting_for_brand, F.text)
async def process_series_brand(message: Message, state: FSMContext):
    brand_name = message.text.strip()
    try:
        brand = await sync_to_async(Brand.objects.get)(name__iexact=brand_name)
    except Brand.DoesNotExist:
        await message.answer("⚠️ Bunday brend topilmadi. Iltimos quyidagi tugmalardan birini bosing:")
        return

    await state.update_data(brand_id=brand.id, brand_name=brand.name)
    await state.set_state(SeriesAddStates.waiting_for_name)

    await message.answer(
        f"✅ Tanlangan brend: <b>{brand.name}</b>\n\n"
        f"Endi ushbu brend uchun <b>model seriyasi nomini</b> kiriting:\n"
        f"<i>(Masalan: Pro seriya, Pro Max seriya, S seriya, A seriya, Redmi Note seriya...)</i>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(SeriesAddStates.waiting_for_name, F.text)
async def process_series_name(message: Message, state: FSMContext):
    series_name = message.text.strip()
    if len(series_name) < 2:
        await message.answer("Nom juda qisqa. Qaytadan kiriting:")
        return

    data = await state.get_data()
    brand_id = data.get('brand_id')
    brand_name = data.get('brand_name')

    exists = await sync_to_async(DeviceSeries.objects.filter(brand_id=brand_id, name__iexact=series_name).exists)()
    if exists:
        await message.answer(f"⚠️ '{series_name}' ushbu brend ostida allaqachon mavjud! Boshqa nom kiriting:")
        return

    series = await sync_to_async(DeviceSeries.objects.create)(
        brand_id=brand_id,
        name=series_name
    )

    await state.clear()
    await message.answer(
        f"🎉 <b>Yangi model seriyasi muvaffaqiyatli saqlandi!</b>\n\n"
        f"🏷 Brend: <b>{brand_name}</b>\n"
        f"📂 Model seriyasi: <b>{series.name}</b>",
        reply_markup=get_section_crud_menu("Model"),
        parse_mode="HTML"
    )


@router.message(F.text == "🗑 Model o‘chirish")
async def delete_series_start(message: Message):
    series_list = await sync_to_async(list)(DeviceSeries.objects.select_related('brand').all().order_by('brand__name', 'name'))
    if not series_list:
        await message.answer("O‘chirish uchun modellar mavjud emas.")
        return

    items = [(f"{s.brand.name} - {s.name}", f"del_series_{s.id}") for s in series_list]
    kb = build_3_row_inline_kb(items, back_callback="", add_cancel=True)

    await message.answer(
        "🗑 <b>O‘chirmoqchi bo‘lgan model seriyangizni tanlang:</b>\n"
        "<i>Eslatma: Model o‘chirilsa, unga tegishli barcha telefonlar ham o‘chadi!</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("del_series_"))
async def process_delete_series(call: CallbackQuery):
    series_id = int(call.data.replace("del_series_", ""))
    try:
        series = await sync_to_async(DeviceSeries.objects.select_related('brand').get)(id=series_id)
        name = f"{series.brand.name} {series.name}"
        await sync_to_async(series.delete)()
        await call.message.edit_text(f"✅ <b>{name}</b> seriyasi muvaffaqiyatli o‘chirildi!", parse_mode="HTML")
    except Exception as e:
        await call.message.edit_text(f"Xatolik: {e}")
    await call.answer()


@router.message(F.text == "✏️ Model tahrirlash")
async def edit_series_start(message: Message):
    series_list = await sync_to_async(list)(DeviceSeries.objects.select_related('brand').all().order_by('brand__name', 'name'))
    if not series_list:
        await message.answer("Tahrirlash uchun modellar mavjud emas.")
        return

    items = [(f"{s.brand.name} - {s.name}", f"edit_series_{s.id}") for s in series_list]
    kb = build_3_row_inline_kb(items, back_callback="", add_cancel=True)

    await message.answer(
        "✏️ <b>Tahrirlamoqchi bo‘lgan model seriyangizni tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("edit_series_"))
async def process_select_series_for_edit(call: CallbackQuery, state: FSMContext):
    series_id = int(call.data.replace("edit_series_", ""))
    try:
        series = await sync_to_async(DeviceSeries.objects.select_related('brand').get)(id=series_id)
        await state.update_data(edit_series_id=series.id, edit_series_name=series.name)
        await state.set_state(SeriesEditStates.waiting_for_new_name)

        await call.message.edit_text(
            f"✏️ <b>'{series.brand.name} - {series.name}' seriyasini tahrirlash</b>\n\n"
            f"Yangi nomini yuboring:",
            parse_mode="HTML"
        )
    except Exception as e:
        await call.message.edit_text(f"Xatolik: {e}")
    await call.answer()


@router.message(SeriesEditStates.waiting_for_new_name, F.text)
async def process_edit_series_name(message: Message, state: FSMContext):
    new_name = message.text.strip()
    if len(new_name) < 2:
        await message.answer("Nom juda qisqa. Qaytadan kiriting:")
        return

    data = await state.get_data()
    series_id = data.get('edit_series_id')

    try:
        series = await sync_to_async(DeviceSeries.objects.get)(id=series_id)
        old_name = series.name
        series.name = new_name
        from django.utils.text import slugify
        series.slug = slugify(new_name)
        await sync_to_async(series.save)()

        await state.clear()
        await message.answer(
            f"✅ <b>Model seriyasi muvaffaqiyatli yangilandi!</b>\n\n"
            f"Eski: <i>{old_name}</i>\n"
            f"Yangi: <b>{new_name}</b>",
            reply_markup=get_section_crud_menu("Model"),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"Xatolik: {e}")

