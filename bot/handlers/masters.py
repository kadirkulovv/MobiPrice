import os
from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from bot.keyboards.main_menu import get_section_crud_menu, get_cancel_menu
from bot.states.admin_states import MasterAddStates, MasterEditStates
from bot.database import TeamMember, sync_to_async
from bot.config import BASE_DIR
from bot.handlers.start import is_admin

router = Router()
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
    if not await is_admin(message.from_user.id, message.from_user.username):
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


@router.message(F.text == "📋 Usta ro‘yxati")
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
        text += (
            f"{idx}. <b>{m.full_name}</b> ({status_info})\n"
            f"   ├ 🔧 <b>Lavozim:</b> {m.role}\n"
            f"   ├ ⚡️ <b>Tajriba:</b> {m.experience}\n"
            f"   └ {photo_info}\n\n"
        )

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "➕ Yangi Usta qo‘shish")
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
        f"🔧 <b>{name} uchun mutaxassislik / lavozimni kiriting:</b>\n"
        "(Masalan: <i>iPhone bo'yicha ekspert</i>, <i>Android va plata ustasi</i>, <i>Lazer va orqa oyna mutaxassisi</i>):",
        parse_mode="HTML"
    )


@router.message(MasterAddStates.waiting_for_role, F.text)
async def process_master_role(message: Message, state: FSMContext):
    role = message.text.strip()
    await state.update_data(role=role)
    await state.set_state(MasterAddStates.waiting_for_experience)
    await message.answer(
        "⚡️ <b>Ushbu mutaxassisning ish stajini (tajribasini) kiriting:</b>\n"
        "(Masalan: <i>7 yillik tajriba</i> yoki <i>5+ yillik tajriba</i>):",
        parse_mode="HTML"
    )


@router.message(MasterAddStates.waiting_for_experience, F.text)
async def process_master_experience(message: Message, state: FSMContext):
    exp = message.text.strip()
    await state.update_data(experience=exp)
    await state.set_state(MasterAddStates.waiting_for_photo)

    await message.answer(
        "📷 <b>Usta fotosuratini yuboring:</b>\n"
        "(Format: rasm yoki hujjat ko'rinishida yuborishingiz mumkin)\n\n"
        "<i>Agar surati hali tayyor bo'lmasa, quyidagi tugmani bosing:</i>",
        reply_markup=get_skip_menu(),
        parse_mode="HTML"
    )


@router.message(MasterAddStates.waiting_for_photo, F.text == "⏩ Surat qo‘ymasdan saqlash")
async def process_master_skip_photo(message: Message, state: FSMContext):
    """Suratsiz saqlash"""
    data = await state.get_data()
    name = data['name']
    role = data['role']
    exp = data['experience']

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
        f"👤 <b>Ism:</b> {name}\n"
        f"🔧 <b>Lavozim:</b> {role}\n"
        f"⚡️ <b>Tajriba:</b> {exp}\n\n"
        f"Saytda <b>'Bizning jamoamiz!'</b> bo'limida avtomatik chiqdi.",
        reply_markup=get_section_crud_menu("Usta"),
        parse_mode="HTML"
    )


@router.message(MasterAddStates.waiting_for_photo, F.photo | F.document)
async def process_master_photo(message: Message, state: FSMContext, bot: Bot):
    """Suratni yuklab olib saqlash"""
    data = await state.get_data()
    name = data['name']
    role = data['role']
    exp = data['experience']

    new_order = await sync_to_async(TeamMember.objects.count)() + 1
    safe_slug = "".join(c if c.isalnum() else "_" for c in name.lower())
    filename = f"master_{safe_slug}_{new_order}.jpg"
    dest_path = MASTERS_MEDIA_DIR / filename

    try:
        if message.photo:
            file_id = message.photo[-1].file_id
        else:
            file_id = message.document.file_id

        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, dest_path)
        rel_photo_path = f"masters/{filename}"
    except Exception as e:
        rel_photo_path = None

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
        f"👤 <b>Ism:</b> {name}\n"
        f"🔧 <b>Lavozim:</b> {role}\n"
        f"⚡️ <b>Tajriba:</b> {exp}\n"
        f"📷 <b>Surat:</b> Yuklandi\n\n"
        f"Saytda <b>'Bizning jamoamiz!'</b> bo'limida yangilandi.",
        reply_markup=get_section_crud_menu("Usta"),
        parse_mode="HTML"
    )


@router.message(F.text == "🗑 Usta o‘chirish")
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
        f"✅ <b>Usta o‘chirildi:</b> {name}",
        parse_mode="HTML"
    )
    await callback.answer("O'chirildi!")
