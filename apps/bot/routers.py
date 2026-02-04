from __future__ import annotations

from aiogram import Router

from apps.bot.handlers.start import create_start_router


def create_bot_router() -> Router:
    router = Router()
    router.include_router(create_start_router())
    return router


router = create_bot_router()
