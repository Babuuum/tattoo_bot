from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    want_custom_sketch = State()
    body_part = State()
    calendar_date = State()
    calendar_time = State()
    promo_code = State()
    confirm = State()
