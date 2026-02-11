from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from core.config.settings import Settings
from core.services.menu import (
    MENU_CHAT,
    MENU_TRYON,
    build_main_menu_keyboard,
)


def create_menu_router() -> Router:
    router = Router()

    @router.message(F.text == MENU_TRYON)
    async def menu_tryon(message: Message) -> None:
        await message.answer("Функция «Примерить тату» пока в разработке.")

    @router.message(F.text == MENU_CHAT)
    async def menu_chat(message: Message) -> None:
        await message.answer("Чат с мастером пока в разработке.")

    @router.message(F.text == "Главное меню")
    async def menu_main(message: Message, settings: Settings) -> None:
        is_admin = message.from_user is not None and (
            message.from_user.id in settings.admin_user_ids
        )
        await message.answer(
            "Главное меню:",
            reply_markup=build_main_menu_keyboard(is_admin=is_admin),
        )

    return router


router = create_menu_router()
