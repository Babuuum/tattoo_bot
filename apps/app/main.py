from __future__ import annotations

import asyncio
import contextlib

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request
from redis.asyncio import Redis

from apps.app.routes.health import router as health_router
from apps.bot.routers import create_bot_router
from core.config.settings import Settings
from core.logging.logger import setup_logging
from core.services.mode import BotMode, get_bot_mode
from infra.db.session import create_async_engine, create_sessionmaker
from infra.redis.client import create_redis


def build_webhook_url(settings: Settings) -> str:
    base = settings.webhook_url.rstrip("/")
    path = settings.webhook_path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"


def create_bot(settings: Settings) -> Bot:
    return Bot(token=settings.bot_token)


def create_dispatcher(*, settings: Settings, redis: Redis) -> Dispatcher:
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)
    dp["settings"] = settings
    dp.include_router(create_bot_router())
    return dp


async def start_polling(bot: Bot, dp: Dispatcher) -> None:
    await dp.start_polling(bot)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    logger = setup_logging(settings.log_level)

    app = FastAPI()
    app.include_router(health_router)

    app.state.settings = settings
    app.state.logger = logger

    engine = create_async_engine(settings.database_url)
    app.state.db_engine = engine
    app.state.session_maker = create_sessionmaker(engine=engine)
    app.state.redis = create_redis(settings.redis_url)

    bot = create_bot(settings)
    dp = create_dispatcher(settings=settings, redis=app.state.redis)
    app.state.bot = bot
    app.state.dispatcher = dp

    mode = get_bot_mode(settings.app_env)
    app.state.bot_mode = mode

    if mode == BotMode.WEBHOOK:

        @app.post(settings.webhook_path)
        async def telegram_webhook(request: Request) -> dict:
            secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if secret != settings.webhook_secret_token:
                raise HTTPException(status_code=403, detail="Forbidden")
            payload = await request.json()
            update = Update.model_validate(payload)
            await dp.feed_update(bot, update)
            return {"ok": True}

    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info("App startup")
        if mode == BotMode.POLLING:
            app.state.polling_task = asyncio.create_task(start_polling(bot, dp))
            return

        if not settings.webhook_url or not settings.webhook_secret_token:
            raise ValueError(
                "WEBHOOK_URL and WEBHOOK_SECRET_TOKEN are required in prod"
            )

        webhook_url = build_webhook_url(settings)
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.webhook_secret_token,
        )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("App shutdown")
        if mode == BotMode.POLLING:
            stop_polling = getattr(dp, "stop_polling", None)
            if callable(stop_polling):
                await stop_polling()
            polling_task = getattr(app.state, "polling_task", None)
            if polling_task is not None:
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task
        else:
            await bot.delete_webhook(drop_pending_updates=False)

        await bot.session.close()

        if hasattr(app.state, "db_engine"):
            await app.state.db_engine.dispose()
        if hasattr(app.state, "redis"):
            await app.state.redis.close()

    return app


app = create_app()
