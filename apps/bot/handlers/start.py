from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from core.config.settings import Settings
from core.services.menu import build_main_menu_keyboard


def create_start_router() -> Router:
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: Message, settings: Settings) -> None:
        is_admin = message.from_user is not None and (
            message.from_user.id in settings.admin_user_ids
        )
        await message.answer(
            "Главное меню:",
            reply_markup=build_main_menu_keyboard(is_admin=is_admin),
        )

    return router


router = create_start_router()
