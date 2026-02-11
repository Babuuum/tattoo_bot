from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AdminCalendarStates(StatesGroup):
    day_off_date = State()

    block_date = State()
    block_time = State()
