from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Optional


def get_main_menu(permissions=None) -> ReplyKeyboardMarkup:
    """Foydalanuvchi roliga moslashtirilgan asosiy admin va menejer paneli menyusi"""
    keyboard = []

    # Agar permissions berilmagan bo'lsa (default fallback)
    is_superadmin = getattr(permissions, 'is_superadmin', False) if permissions else True
    can_site = getattr(permissions, 'can_manage_site', False) if permissions else True
    can_leads = getattr(permissions, 'can_handle_leads', False) if permissions else True
    can_admins = getattr(permissions, 'can_manage_admins', False) if permissions else True

    # 1. Zayavkalar va Statistika (Faqat Menejer yoki Superadmin yoki Ikkalasi)
    top_row = []
    if can_leads:
        top_row.append(KeyboardButton(text="📦 Buyurtmalar (CRM)"))
    top_row.append(KeyboardButton(text="📊 Statistika"))
    if top_row:
        keyboard.append(top_row)

    # 2. Sayt Resurslari (Faqat Admin, Superadmin yoki Ikkalasi)
    if can_site:
        keyboard.append([
            KeyboardButton(text="🏷 Brendlar"),
            KeyboardButton(text="📂 Modellar"),
            KeyboardButton(text="📱 Telefonlar"),
        ])
        keyboard.append([
            KeyboardButton(text="🔧 Muammolar"),
            KeyboardButton(text="⚖️ Solishtirish (Narxlar)"),
        ])
        keyboard.append([
            KeyboardButton(text="📁 Excel Import / Export"),
            KeyboardButton(text="👨‍🔧 Ustalar (Jamoa)"),
        ])

    # 3. Faqat Glavniy Admin (Superadmin) uchun: Xodimlar boshqaruvi
    admin_row = []
    if can_admins:
        admin_row.append(KeyboardButton(text="👥 Xodimlar (Admin / Menejer)"))
        admin_row.append(KeyboardButton(text="💾 Zaxira (Backup)"))
    elif can_site:
        admin_row.append(KeyboardButton(text="💾 Zaxira (Backup)"))

    if admin_row:
        keyboard.append(admin_row)

    # 4. Yangilash
    keyboard.append([KeyboardButton(text="🔄 Yangilash")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)





def get_section_crud_menu(section_title: str) -> ReplyKeyboardMarkup:
    """Har bir bo'lim ichidagi to'liq CRUD amallari (Create, Read, Update, Delete)"""
    keyboard = [
        [
            KeyboardButton(text=f"📋 {section_title} ro‘yxati"),
            KeyboardButton(text=f"➕ Yangi {section_title} qo‘shish"),
        ],
        [
            KeyboardButton(text=f"✏️ {section_title} tahrirlash"),
            KeyboardButton(text=f"🗑 {section_title} o‘chirish"),
        ],
        [
            KeyboardButton(text="🔙 Asosiy menyu"),
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_cancel_menu() -> ReplyKeyboardMarkup:
    """Jarayonni bekor qilish tugmasi"""
    keyboard = [
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
