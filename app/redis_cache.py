from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

_redis: Any | None = None


async def get_redis():
    global _redis
    settings = get_settings()
    if not settings.redis_url:
        return None
    if _redis is not None:
        return _redis
    try:
        import redis.asyncio as redis
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
        await _redis.ping()
        return _redis
    except Exception as exc:
        logger.warning("Redis unavailable, using in-memory fallback: %s", exc)
        _redis = None
        return None


async def redis_health() -> bool:
    client = await get_redis()
    if client is None:
        return False
    try:
        return bool(await client.ping())
    except Exception as exc:
        logger.debug("Redis health check failed: %s", exc, exc_info=True)
        return False


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        try:
            await _redis.aclose()
        except Exception as exc:
            logger.debug("Redis close failed: %s", exc, exc_info=True)
        _redis = None
