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
        user_id = message.from_user.id if message.from_user is not None else None
        is_admin = settings.is_admin_user(user_id)
        await message.answer(
            "Главное меню:",
            reply_markup=build_main_menu_keyboard(
                is_admin=is_admin,
                mini_app_url=settings.resolved_mini_app_url,
            ),
        )

    return router


router = create_start_router()
