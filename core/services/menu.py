from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

MENU_BOOK = "Записаться на сеанс"
MENU_TRYON = "Примерить тату"
MENU_GALLERY = "Галерея"
MENU_CHAT = "Чат с мастером"
MENU_ADMIN = "Админка"


def build_main_menu_keyboard(*, is_admin: bool) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = [
        [KeyboardButton(text=MENU_BOOK)],
        [KeyboardButton(text=MENU_TRYON)],
        [KeyboardButton(text=MENU_GALLERY)],
        [KeyboardButton(text=MENU_CHAT)],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=MENU_ADMIN)])

    rows.append([KeyboardButton(text="Главное меню")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
