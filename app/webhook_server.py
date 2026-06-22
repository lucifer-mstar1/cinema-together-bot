from __future__ import annotations

import logging

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request

from app.bot import create_bot, create_dispatcher
from app.config import get_settings
from app.db import init_db, close_db, db_health
from app.logging_config import configure_logging
from app.redis_cache import close_redis, redis_health
from app.texts import validate_texts

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(title="CinemaTogether Bot", version="30.0.0")
bot = create_bot()
dp = create_dispatcher()


@app.on_event("startup")
async def startup() -> None:
    configure_logging()
    text_errors = validate_texts()
    if text_errors:
        for err in text_errors:
            logger.error("TEXT VALIDATION: %s", err)
        raise RuntimeError(f"texts.py has {len(text_errors)} missing translations. Fix before launch.")
    logger.info(
        "Webhook mode detected. Matching queue, active-match ownership, pending watch intents, and FSM are durable when "
        "DATABASE_URL and REDIS_URL are configured. Keep normal single-instance deployment unless you have tested "
        "Telegram update ordering and DB isolation for your hosting stack."
    )
    await init_db()
    if not await redis_health():
        raise RuntimeError("Redis is required for webhook mode. Start Redis and set REDIS_URL correctly.")
    if not settings.webhook_url:
        raise RuntimeError("WEBHOOK_BASE_URL is required when BOT_MODE=webhook")
    await bot.set_webhook(
        settings.webhook_url,
        secret_token=settings.webhook_secret,
        drop_pending_updates=settings.drop_pending_updates,
        allowed_updates=dp.resolve_used_update_types(),
    )
    logger.info("Webhook set to %s", settings.webhook_url)


@app.on_event("shutdown")
async def shutdown() -> None:
    try:
        await bot.delete_webhook(drop_pending_updates=False)
    finally:
        await close_redis()
        await close_db()
        await bot.session.close()


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "ok": True,
        "database": await db_health(),
        "redis": await redis_health(),
        "mode": settings.bot_mode,
        "env": settings.app_env,
    }


@app.post(settings.webhook_path)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    if settings.webhook_secret and x_telegram_bot_api_secret_token != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})

    await dp.feed_update(bot, update)
    return {"ok": True}
