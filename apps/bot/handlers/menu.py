from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from core.config.settings import Settings
from core.services.menu import (
    MENU_CHAT,
    MENU_TRYON,
    build_main_menu_keyboard,
)
from core.services.webapp_payload import parse_web_app_data, render_quote_summary


def create_menu_router() -> Router:
    router = Router()

    @router.message(F.text == MENU_TRYON)
    async def menu_tryon(message: Message) -> None:
        await message.answer("Нажмите кнопку «Примерить тату» в меню ниже.")

    @router.message(F.web_app_data)
    async def webapp_data_message(message: Message) -> None:
        if message.web_app_data is None:
            return
        try:
            quote = parse_web_app_data(message.web_app_data.data)
        except ValueError:
            await message.answer(
                "Не удалось обработать данные из Mini App. Повторите расчёт."
            )
            return
        await message.answer(render_quote_summary(quote))

    @router.message(F.text == MENU_CHAT)
    async def menu_chat(message: Message) -> None:
        await message.answer("Чат с мастером пока в разработке.")

    @router.message(F.text == "Главное меню")
    async def menu_main(message: Message, settings: Settings) -> None:
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


router = create_menu_router()
