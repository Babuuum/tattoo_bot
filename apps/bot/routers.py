from __future__ import annotations

from aiogram import Router

from apps.bot.handlers.admin_catalog import create_admin_catalog_router
from apps.bot.handlers.booking import create_booking_router
from apps.bot.handlers.gallery import create_gallery_router
from apps.bot.handlers.menu import create_menu_router
from apps.bot.handlers.start import create_start_router


def create_bot_router() -> Router:
    router = Router()
    router.include_router(create_start_router())
    router.include_router(create_booking_router())
    router.include_router(create_gallery_router())
    router.include_router(create_admin_catalog_router())
    router.include_router(create_menu_router())
    return router


router = create_bot_router()
