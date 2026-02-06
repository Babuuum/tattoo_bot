from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AdminCatalogStates(StatesGroup):
    add_style_name = State()

    add_tattoo_style = State()
    add_tattoo_name = State()
    add_tattoo_price = State()
    add_tattoo_photo = State()
