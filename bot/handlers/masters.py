import os
import time
import html
import logging
from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, Document, PhotoSize
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_section_crud_menu, get_cancel_menu
from bot.states.admin_states import MasterAddStates, MasterEditStates
from bot.database import TeamMember, sync_to_async
from bot.config import BASE_DIR
from bot.handlers.start import is_admin, is_site_admin

router = Router()
logger = logging.getLogger("mobiprice_bot")

MASTERS_MEDIA_DIR = BASE_DIR / 'media' / 'masters'
os.makedirs(MASTERS_MEDIA_DIR, exist_ok=True)


def get_skip_menu() -> ReplyKeyboardMarkup:
    """Suratni o'tkazib yuborish tugmasi"""
    keyboard = [
        [KeyboardButton(text="⏩ Surat qo‘ymasdan saqlash")],
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


@router.message(F.text == "👨‍🔧 Ustalar (Jamoa)")
async def masters_menu(message: Message, state: FSMContext):
    """Ustalar boshqaruv menyusi"""
    if not await is_site_admin(message.from_user.id, message.from_user.username):
        await message.answer("⛔️ Bu bo‘lim faqat Sayt Administratorlari va Bosh Admin uchun!")
        return

    await state.clear()
    await message.answer(
        "👨‍🔧 <b>Ustalar va Mutaxassislar (Jamoa) bo‘limi</b>\n\n"
        "Saytdagi <b>'Bizning jamoamiz!'</b> blokida chiqadigan mutaxassislarni boshqarish:\n"
        "• Nomlari va lavozimlari (masalan: <i>iPhone bo'yicha ekspert</i>)\n"
        "• Ish tajribasi (masalan: <i>7 yillik tajriba</i>)\n"
        "• Fotosuratlari\n\n"
        "Quyidagi amallardan birini tanlang 👇",
        reply_markup=get_section_crud_menu("Usta"),
        parse_mode="HTML"
    )


@router.message(F.text.in_(["📋 Usta ro‘yxati", "📋 Usta ro'yxati"]))
async def list_masters(message: Message):
    """Barcha ustalar ro'yxatini ko'rish"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    masters = await sync_to_async(list)(TeamMember.objects.all().order_by('order', 'id'))

    if not masters:
        await message.answer("Bazada hozircha birorta ham usta kiritilmagan.")
        return

    text = "📋 <b>Mavjud Ustalar (Jamoa) ro‘yxati:</b>\n\n"
    for idx, m in enumerate(masters, 1):
        photo_info = "📷 Surat bor" if m.photo else "👤 Standart avatar"
        status_info = "🟢 Faol" if m.is_active else "🔴 Nofaol"
        clean_name = html.escape(m.full_name or '')
        clean_role = html.escape(m.role or '')
        clean_exp = html.escape(m.experience or '')
        text += (
            f"{idx}. <b>{clean_name}</b> ({status_info})\n"
            f"   ├ 🔧 <b>Lavozim:</b> {clean_role}\n"
            f"   ├ ⚡️ <b>Tajriba:</b> {clean_exp}\n"
            f"   └ {photo_info}\n\n"
        )

    await message.answer(text, parse_mode="HTML")


@router.message(F.text.in_(["➕ Yangi Usta qo‘shish", "➕ Yangi Usta qo'shish"]))
async def add_master_start(message: Message, state: FSMContext):
    """Yangi usta qo'shish jarayoni"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    await state.set_state(MasterAddStates.waiting_for_name)
    await message.answer(
        "✍️ <b>Usta / Mutaxassisning to‘liq ismini kiriting:</b>\n"
        "(Masalan: <i>Kurbanov Muzafar</i> yoki <i>Murodjon Milyazov</i>)",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(MasterAddStates.waiting_for_name, F.text)
async def process_master_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Ism kamida 2 ta belgidan iborat bo‘lishi kerak. Qaytadan kiriting:")
        return

    await state.update_data(name=name)
    await state.set_state(MasterAddStates.waiting_for_role)
    await message.answer(
        f"🔧 <b>{html.escape(name)} uchun mutaxassislik / lavozimni kiriting:</b>\n"
        "(Masalan: <i>iPhone bo'yicha ekspert</i>, <i>Android va plata ustasi</i>, <i>Lazer va orqa oyna mutaxassisi</i>):",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(MasterAddStates.waiting_for_role, F.text)
async def process_master_role(message: Message, state: FSMContext):
    role = message.text.strip()
    if len(role) < 2:
        await message.answer("Lavozim kamida 2 ta belgidan iborat bo‘lishi kerak. Qaytadan kiriting:")
        return

    await state.update_data(role=role)
    await state.set_state(MasterAddStates.waiting_for_experience)
    await message.answer(
        "⚡️ <b>Ushbu mutaxassisning ish stajini (tajribasini) kiriting:</b>\n"
        "(Masalan: <i>7 yillik tajriba</i> yoki <i>5+ yillik tajriba</i>):",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )


@router.message(MasterAddStates.waiting_for_experience, F.text)
async def process_master_experience(message: Message, state: FSMContext):
    exp = message.text.strip()
    await state.update_data(experience=exp)
    await state.set_state(MasterAddStates.waiting_for_photo)

    await message.answer(
        "📷 <b>Usta fotosuratini yuboring:</b>\n"
        "(Format: rasm yoki fayl ko'rinishida yuborishingiz mumkin)\n\n"
        "<i>Agar surati hali tayyor bo'lmasa, quyidagi tugmani bosing:</i>",
        reply_markup=get_skip_menu(),
        parse_mode="HTML"
    )


@router.message(MasterAddStates.waiting_for_photo, F.text == "⏩ Surat qo‘ymasdan saqlash")
async def process_master_skip_photo(message: Message, state: FSMContext):
    """Suratsiz saqlash"""
    data = await state.get_data()
    name = data.get('name', 'Noma\'lum')
    role = data.get('role', 'Mutaxassis')
    exp = data.get('experience', '5+ yillik tajriba')

    new_order = await sync_to_async(TeamMember.objects.count)() + 1

    await sync_to_async(TeamMember.objects.create)(
        full_name=name,
        role=role,
        experience=exp,
        order=new_order,
        is_active=True
    )

    await state.clear()
    await message.answer(
        f"✅ <b>Yangi usta muvaffaqiyatli saqlandi!</b>\n\n"
        f"👤 <b>Ism:</b> {html.escape(name)}\n"
        f"🔧 <b>Lavozim:</b> {html.escape(role)}\n"
        f"⚡️ <b>Tajriba:</b> {html.escape(exp)}\n\n"
        f"Saytda <b>'Bizning jamoamiz!'</b> bo'limida avtomatik chiqdi.",
        reply_markup=get_section_crud_menu("Usta"),
        parse_mode="HTML"
    )


@router.message(MasterAddStates.waiting_for_photo, F.photo | F.document)
async def process_master_photo(message: Message, state: FSMContext, bot: Bot):
    """Suratni yuklab olib saqlash"""
    data = await state.get_data()
    name = data.get('name', 'usta')
    role = data.get('role', 'Mutaxassis')
    exp = data.get('experience', '5+ yillik tajriba')

    # Resolve photo or document
    if message.photo:
        file_obj = message.photo[-1]
        ext = ".jpg"
    elif message.document:
        doc: Document = message.document
        mime = (doc.mime_type or "").lower()
        fname = (doc.file_name or "").lower()
        if not (mime.startswith("image/") or fname.endswith(('.jpg', '.jpeg', '.png', '.webp', '.heic'))):
            await message.answer("⚠️ Iltimos, faqat rasm faylini yuboring (JPG, PNG, WEBP):")
            return
        file_obj = doc
        ext = os.path.splitext(doc.file_name)[1].lower() if doc.file_name else ".jpg"
        if ext not in ('.jpg', '.jpeg', '.png', '.webp', '.heic'):
            ext = ".jpg"
    else:
        await message.answer("⚠️ Iltimos, usta fotosuratini yuboring:")
        return

    new_order = await sync_to_async(TeamMember.objects.count)() + 1
    safe_slug = "".join(c if c.isalnum() else "_" for c in name.lower())
    timestamp = int(time.time())
    filename = f"master_{safe_slug}_{new_order}_{timestamp}{ext}"
    dest_path = MASTERS_MEDIA_DIR / filename

    try:
        await bot.download(file_obj, destination=dest_path)
        rel_photo_path = f"masters/{filename}"
    except Exception as e:
        logger.error(f"Usta rasmini saqlashda xatolik: {e}", exc_info=True)
        await message.answer(
            f"⚠️ Suratni yuklab olishda xatolik yuz berdi: {e}\n"
            f"Iltimos, qaytadan yuboring yoki '⏩ Surat qo‘ymasdan saqlash' tugmasini bosing:",
            reply_markup=get_skip_menu()
        )
        return

    await sync_to_async(TeamMember.objects.create)(
        full_name=name,
        role=role,
        experience=exp,
        photo=rel_photo_path,
        order=new_order,
        is_active=True
    )

    await state.clear()
    await message.answer(
        f"✅ <b>Yangi usta fotosurati bilan saqlandi!</b>\n\n"
        f"👤 <b>Ism:</b> {html.escape(name)}\n"
        f"🔧 <b>Lavozim:</b> {html.escape(role)}\n"
        f"⚡️ <b>Tajriba:</b> {html.escape(exp)}\n"
        f"📷 <b>Surat:</b> Muvaffaqiyatli yuklandi\n\n"
        f"Saytda <b>'Bizning jamoamiz!'</b> bo'limida yangilandi.",
        reply_markup=get_section_crud_menu("Usta"),
        parse_mode="HTML"
    )


@router.message(MasterAddStates.waiting_for_photo)
async def invalid_master_add_photo(message: Message):
    """Kutilmagan matn kelganda ogohlantirish"""
    await message.answer(
        "📷 Iltimos, usta fotosuratini (rasm yoki fayl ko‘rinishida) yuboring,\n"
        "yoki suratsiz davom etish uchun '⏩ Surat qo‘ymasdan saqlash' tugmasini bosing:",
        reply_markup=get_skip_menu()
    )


@router.message(F.text.func(lambda t: t and "Usta" in t and "tahrirlash" in t))
async def edit_master_start(message: Message, state: FSMContext):
    """Ustani tahrirlashni boshlash"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    await state.clear()
    masters = await sync_to_async(list)(TeamMember.objects.all().order_by('order', 'id'))
    if not masters:
        await message.answer("Tahrirlash uchun ustalar mavjud emas.")
        return

    buttons = []
    for m in masters:
        status_icon = "🟢" if m.is_active else "🔴"
        buttons.append([InlineKeyboardButton(text=f"{status_icon} {m.full_name} ({m.role})", callback_data=f"edit_m:{m.id}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        "✏️ <b>Tahrirlamoqchi bo‘lgan ustangizni tanlang:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("edit_m:"))
async def process_select_master_for_edit(call: CallbackQuery, state: FSMContext = None):
    """Tanlangan usta tafsilotlari va tahrirlash menyusi"""
    master_id = int(call.data.split(":")[1])
    master = await sync_to_async(TeamMember.objects.filter(id=master_id).first)()
    if not master:
        await call.answer("Usta topilmadi.", show_alert=True)
        return

    status_str = "🟢 Faol (Saytda ko‘rinadi)" if master.is_active else "🔴 Nofaol (Yashiringan)"
    photo_str = "📷 Yuklangan" if master.photo else "👤 Standart avatar"

    clean_name = html.escape(master.full_name or '')
    clean_role = html.escape(master.role or '')
    clean_exp = html.escape(master.experience or '')

    text = (
        f"👨‍🔧 <b>Usta ma'lumotlari:</b>\n\n"
        f"👤 <b>Ism:</b> {clean_name}\n"
        f"🔧 <b>Lavozim:</b> {clean_role}\n"
        f"⚡️ <b>Tajriba:</b> {clean_exp}\n"
        f"🚦 <b>Holat:</b> {status_str}\n"
        f"🖼 <b>Surat:</b> {photo_str}\n\n"
        f"Qaysi ma'lumotni o‘zgartirmoqchisiz? Quyidagi tugmalardan birini tanlang 👇"
    )

    toggle_btn_text = "🔴 Nofaol qilish" if master.is_active else "🟢 Faol qilish"

    buttons = [
        [
            InlineKeyboardButton(text="👤 Ismni o‘zgartirish", callback_data=f"medit_field:{master.id}:name"),
            InlineKeyboardButton(text="🔧 Lavozimni o‘zgartirish", callback_data=f"medit_field:{master.id}:role"),
        ],
        [
            InlineKeyboardButton(text="⚡️ Tajribani o‘zgartirish", callback_data=f"medit_field:{master.id}:exp"),
            InlineKeyboardButton(text="📷 Suratni yangilash", callback_data=f"medit_field:{master.id}:photo"),
        ],
        [
            InlineKeyboardButton(text=toggle_btn_text, callback_data=f"mtoggle:{master.id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Ustalar ro‘yxatiga qaytish", callback_data="medit_list_back")
        ]
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("mtoggle:"))
async def process_toggle_master_active(call: CallbackQuery):
    """Usta holatini (Faol/Nofaol) bir zumda o'zgartirish"""
    master_id = int(call.data.split(":")[1])
    master = await sync_to_async(TeamMember.objects.filter(id=master_id).first)()
    if not master:
        await call.answer("Usta topilmadi.", show_alert=True)
        return

    master.is_active = not master.is_active
    await sync_to_async(master.save)()
    await call.answer("Holati o'zgartirildi!")
    call.data = f"edit_m:{master.id}"
    await process_select_master_for_edit(call)


@router.callback_query(F.data == "medit_list_back")
async def process_edit_master_back(call: CallbackQuery, state: FSMContext):
    """Tahrirlashda ro'yxatga qaytish"""
    await state.clear()
    masters = await sync_to_async(list)(TeamMember.objects.all().order_by('order', 'id'))
    buttons = []
    for m in masters:
        status_icon = "🟢" if m.is_active else "🔴"
        buttons.append([InlineKeyboardButton(text=f"{status_icon} {m.full_name} ({m.role})", callback_data=f"edit_m:{m.id}")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("✏️ <b>Tahrirlamoqchi bo‘lgan ustangizni tanlang:</b>", reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("medit_field:"))
async def process_medit_field(call: CallbackQuery, state: FSMContext):
    """Qaysi maydonni tahrirlashni boshlash"""
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer("Xato so‘rov.", show_alert=True)
        return

    _, master_id, field = parts
    master = await sync_to_async(TeamMember.objects.filter(id=int(master_id)).first)()
    if not master:
        await call.answer("Usta topilmadi.", show_alert=True)
        return

    clean_name = html.escape(master.full_name or '')
    await state.update_data(edit_master_id=int(master_id), edit_field=field)

    prompts = {
        'name': f"✍️ <b>'{clean_name}' uchun yangi ismni yozing:</b>",
        'role': f"🔧 <b>'{clean_name}' uchun yangi lavozim / mutaxassislikni yozing:</b>\n(Masalan: <i>iPhone bo'yicha ekspert</i>)",
        'exp': f"⚡️ <b>'{clean_name}' uchun yangi ish stajini (tajribasini) yozing:</b>\n(Masalan: <i>8 yillik tajriba</i>)",
        'photo': f"📷 <b>'{clean_name}' uchun yangi fotosurat yuboring:</b>\n(Rasm yoki hujjat sifatida)",
    }

    if field == 'photo':
        await state.set_state(MasterEditStates.waiting_for_new_photo)
    else:
        await state.set_state(MasterEditStates.waiting_for_new_data)

    await call.message.answer(
        prompts.get(field, "Yangi qiymatni kiriting:"),
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(MasterEditStates.waiting_for_new_data, F.text)
async def process_save_master_text(message: Message, state: FSMContext):
    """Matnli maydonlarni saqlash (Ism, Lavozim, Tajriba)"""
    new_val = message.text.strip()
    data = await state.get_data()
    master_id = data.get('edit_master_id')
    field = data.get('edit_field')

    master = await sync_to_async(TeamMember.objects.filter(id=master_id).first)()
    if not master:
        await state.clear()
        await message.answer("Usta topilmadi.", reply_markup=get_section_crud_menu("Usta"))
        return

    if field == 'name':
        master.full_name = new_val
        field_label = "Ism"
    elif field == 'role':
        master.role = new_val
        field_label = "Lavozim"
    elif field == 'exp':
        master.experience = new_val
        field_label = "Tajriba"
    else:
        field_label = "Ma'lumot"

    await sync_to_async(master.save)()
    await state.clear()

    await message.answer(
        f"✅ <b>Usta ma'lumoti muvaffaqiyatli yangilandi!</b>\n\n"
        f"👤 <b>Usta:</b> {html.escape(master.full_name)}\n"
        f"📝 <b>O‘zgartirildi:</b> {field_label}\n"
        f"🔄 <b>Yangi qiymat:</b> {html.escape(new_val)}\n\n"
        f"Saytda <b>'Bizning jamoamiz!'</b> bo‘limida avtomatik yangilandi.",
        reply_markup=get_section_crud_menu("Usta"),
        parse_mode="HTML"
    )


@router.message(MasterEditStates.waiting_for_new_photo, F.photo | F.document)
async def process_save_master_photo(message: Message, state: FSMContext, bot: Bot):
    """Yangi fotosuratni saqlash"""
    data = await state.get_data()
    master_id = data.get('edit_master_id')
    master = await sync_to_async(TeamMember.objects.filter(id=master_id).first)()
    if not master:
        await state.clear()
        await message.answer("Usta topilmadi.", reply_markup=get_section_crud_menu("Usta"))
        return

    # Resolve photo or document
    if message.photo:
        file_obj = message.photo[-1]
        ext = ".jpg"
    elif message.document:
        doc: Document = message.document
        mime = (doc.mime_type or "").lower()
        fname = (doc.file_name or "").lower()
        if not (mime.startswith("image/") or fname.endswith(('.jpg', '.jpeg', '.png', '.webp', '.heic'))):
            await message.answer("⚠️ Iltimos, faqat rasm faylini yuboring (JPG, PNG, WEBP):")
            return
        file_obj = doc
        ext = os.path.splitext(doc.file_name)[1].lower() if doc.file_name else ".jpg"
        if ext not in ('.jpg', '.jpeg', '.png', '.webp', '.heic'):
            ext = ".jpg"
    else:
        await message.answer("⚠️ Iltimos, fotosurat yuboring:")
        return

    safe_slug = "".join(c if c.isalnum() else "_" for c in master.full_name.lower())
    timestamp = int(time.time())
    filename = f"master_{safe_slug}_{master.id}_{timestamp}{ext}"
    dest_path = MASTERS_MEDIA_DIR / filename

    try:
        await bot.download(file_obj, destination=dest_path)
        master.photo = f"masters/{filename}"
        await sync_to_async(master.save)()

        await state.clear()
        await message.answer(
            f"✅ <b>'{html.escape(master.full_name)}' fotosurati muvaffaqiyatli yangilandi!</b>\n\n"
            f"Saytda <b>'Bizning jamoamiz!'</b> bo‘limida yangi surat bilan chiqdi.",
            reply_markup=get_section_crud_menu("Usta"),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Suratni saqlashda xatolik: {e}", exc_info=True)
        await message.answer(
            f"⚠️ Suratni saqlashda xatolik: {e}\nIltimos qaytadan yuboring:",
            reply_markup=get_cancel_menu()
        )


@router.message(MasterEditStates.waiting_for_new_photo)
async def invalid_master_edit_photo(message: Message):
    """Fotosurat kutilganda matn yuborilsa ogohlantirish"""
    await message.answer(
        "📷 Iltimos, usta uchun yangi fotosurat yuboring (rasm yoki fayl ko‘rinishida).\n"
        "Yoki jarayonni to‘xtatish uchun '❌ Bekor qilish' tugmasini bosing:",
        reply_markup=get_cancel_menu()
    )


@router.message(F.text.in_(["🗑 Usta o‘chirish", "🗑 Usta o'chirish"]))
async def delete_master_start(message: Message):
    """Ustani o'chirish"""
    if not await is_admin(message.from_user.id, message.from_user.username):
        return

    masters = await sync_to_async(list)(TeamMember.objects.all().order_by('order', 'id'))
    if not masters:
        await message.answer("O‘chirish uchun birorta ham usta topilmadi.")
        return

    buttons = []
    for m in masters:
        buttons.append([InlineKeyboardButton(text=f"❌ {m.full_name} ({m.role})", callback_data=f"del_master:{m.id}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("🗑 <b>O‘chirmoqchi bo‘lgan ustangizni tanlang:</b>", reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("del_master:"))
async def process_delete_master(callback: CallbackQuery):
    master_id = int(callback.data.split(":")[1])
    master_obj = await sync_to_async(TeamMember.objects.filter(id=master_id).first)()

    if not master_obj:
        await callback.answer("Usta topilmadi.", show_alert=True)
        return

    name = master_obj.full_name
    await sync_to_async(master_obj.delete)()

    await callback.message.edit_text(
        f"✅ <b>Usta o‘chirildi:</b> {html.escape(name)}",
        parse_mode="HTML"
    )
    await callback.answer("O'chirildi!")
