from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """Asosiy admin paneli menyusi"""
    keyboard = [
        [
            KeyboardButton(text="📦 Buyurtmalar (CRM)"),
            KeyboardButton(text="📊 Statistika"),
        ],
        [
            KeyboardButton(text="🏷 Brendlar"),
            KeyboardButton(text="📂 Modellar"),
            KeyboardButton(text="📱 Telefonlar"),
        ],
        [
            KeyboardButton(text="🔧 Muammolar"),
            KeyboardButton(text="⚖️ Solishtirish (Narxlar)"),
        ],
        [
            KeyboardButton(text="📁 Excel Import / Export"),
            KeyboardButton(text="👨‍🔧 Ustalar (Jamoa)"),
        ],
        [
            KeyboardButton(text="👥 Adminlar"),
            KeyboardButton(text="🔄 Yangilash"),
        ]
    ]
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
