from typing import List, Tuple
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


def chunk_list(items: list, chunk_size: int = 3) -> List[list]:
    """Ro'yxatni berilgan o'lchamda (3 tadan) qatorlarga bo'lish"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def build_3_row_reply_kb(items: List[str], add_cancel: bool = True) -> ReplyKeyboardMarkup:
    """Matnli tugmalarni har bir qatorda maksimal 3 tadan qilib ReplyKeyboard yasash"""
    buttons = [KeyboardButton(text=item) for item in items]
    keyboard = chunk_list(buttons, 3)

    if add_cancel:
        keyboard.append([KeyboardButton(text="❌ Bekor qilish")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def build_3_row_inline_kb(
    items: List[Tuple[str, str]],
    back_callback: str = "main_menu",
    add_cancel: bool = True
) -> InlineKeyboardMarkup:
    """Inline tugmalarni har bir qatorda 3 tadan qilib InlineKeyboard yasash: [(label, callback_data), ...]"""
    buttons = [InlineKeyboardButton(text=label, callback_data=cb_data) for label, cb_data in items]
    keyboard = chunk_list(buttons, 3)

    nav_row = []
    if add_cancel:
        nav_row.append(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action"))
    if back_callback:
        nav_row.append(InlineKeyboardButton(text="🔙 Orqaga", callback_data=back_callback))

    if nav_row:
        keyboard.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
