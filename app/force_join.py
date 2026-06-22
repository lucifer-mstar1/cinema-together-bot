from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, TelegramObject

from app.config import get_settings
from app.db import SessionLocal
from app.keyboards import language_kb, menu_kb
from app.models import User
from app.redis_cache import get_redis
from app.states import Onboarding
from app.services import get_or_create_user, normalize_watch_start_arg, save_pending_watch_intent
from app.texts import t

logger = logging.getLogger(__name__)
settings = get_settings()

FORCE_JOIN_CHECK_CALLBACK = "forcejoin:check"
_MEMBERSHIP_CACHE: dict[tuple[int, str], tuple[float, bool]] = {}


@dataclass(frozen=True)
class RequiredChat:
    chat_id: str | int
    title: str
    url: str


def _looks_like_placeholder_or_invalid(raw: str) -> bool:
    clean = (raw or "").strip()
    if not clean:
        return True
    lowered = clean.lower()
    return any(token in lowered for token in ("your_channel", "invitelink", "example", "change-me"))


def _is_private_invite_url(value: str) -> bool:
    clean = (value or "").strip().lower()
    return clean.startswith(("https://t.me/+", "http://t.me/+", "t.me/+", "https://telegram.me/+", "http://telegram.me/+", "telegram.me/+"))


def _looks_malformed_join_url(value: str) -> bool:
    clean = (value or "").strip().lower()
    if not clean:
        return False
    return any(
        bad in clean
        for bad in (
            "https://https://",
            "http://http://",
            "https://http://",
            "http://https://",
            "t.me/https://",
            "t.me/http://",
            "telegram.me/https://",
            "telegram.me/http://",
        )
    )

def _split_required_chat(raw: str) -> RequiredChat | None:
    """Parse one FORCE_JOIN_CHATS item without requiring a fragile format.

    Supported examples:
      @public_channel
      https://t.me/public_channel
      -1001234567890|https://t.me/+invite|Private group
    """
    item = (raw or "").strip()
    if not item or _looks_like_placeholder_or_invalid(item):
        return None

    parts = [p.strip() for p in item.split("|")]
    chat_ref = parts[0]
    url = parts[1] if len(parts) > 1 else ""
    title = parts[2] if len(parts) > 2 else ""

    if _looks_malformed_join_url(chat_ref) or _looks_malformed_join_url(url):
        logger.error(
            "Invalid FORCE_JOIN item %r: malformed invite/link. Use a single clean URL like https://t.me/+InviteCode",
            item,
        )
        return None

    # Telegram cannot verify membership from a private invite URL alone.
    # Required private chats must use: -100CHAT_ID|https://t.me/+invite|Title
    if _is_private_invite_url(chat_ref):
        logger.error(
            "Invalid FORCE_JOIN item %r: private invite links need numeric -100 chat_id. "
            "Use -100CHAT_ID|%s|Title",
            item,
            chat_ref if chat_ref.startswith("http") else "https://" + chat_ref,
        )
        return None

    if chat_ref.startswith(("https://t.me/", "http://t.me/", "https://telegram.me/", "http://telegram.me/")):
        url = url or chat_ref
        username = chat_ref.rstrip("/").split("/")[-1]
        chat_ref = "@" + username if username and not username.startswith("+") else chat_ref
        title = title or username or "Telegram channel/group"
    elif chat_ref.startswith(("t.me/", "telegram.me/")):
        url = url or "https://" + chat_ref
        username = chat_ref.rstrip("/").split("/")[-1]
        chat_ref = "@" + username if username and not username.startswith("+") else chat_ref
        title = title or username or "Telegram channel/group"
    elif chat_ref.startswith("@"):
        username = chat_ref.lstrip("@")
        url = url or f"https://t.me/{username}"
        title = title or username
    else:
        title = title or chat_ref

    # Numeric chat IDs should be passed to Telegram as int; @username stays str.
    parsed_ref: str | int = int(chat_ref) if chat_ref.lstrip("-").isdigit() else chat_ref
    return RequiredChat(chat_id=parsed_ref, title=title, url=url)




def validate_force_join_configuration() -> list[str]:
    errors: list[str] = []
    raw_items = settings.force_join_items
    if not raw_items:
        return []
    parsed_count = 0
    for raw in raw_items:
        item = (raw or "").strip()
        parts = [p.strip() for p in item.split("|")]
        first = parts[0] if parts else ""
        url = parts[1] if len(parts) > 1 else ""
        if _looks_malformed_join_url(first) or _looks_malformed_join_url(url):
            errors.append(
                f"Invalid FORCE_JOIN item {item!r}: malformed invite/link. "
                "Use one clean URL like https://t.me/+REAL_INVITE_LINK."
            )
            continue
        if _is_private_invite_url(first):
            errors.append(
                f"Invalid FORCE_JOIN item {item!r}: private invite links cannot be verified alone. "
                "Use -100CHAT_ID|https://t.me/+REAL_INVITE_LINK|Title instead."
            )
            continue
        if _split_required_chat(item):
            parsed_count += 1
    if settings.force_join_active and parsed_count == 0:
        errors.append("FORCE_JOIN is active but no valid required chats were parsed. Check FORCE_JOIN_CHATS / CHANNELS / GROUPS.")
    return errors

def required_chats() -> list[RequiredChat]:
    if not settings.force_join_active:
        return []
    chats: list[RequiredChat] = []
    seen: set[str] = set()
    for raw in settings.force_join_items:
        parsed = _split_required_chat(raw)
        if not parsed:
            continue
        key = str(parsed.chat_id)
        if key in seen:
            continue
        seen.add(key)
        chats.append(parsed)
    return chats


def is_force_join_exempt_user(from_user: Any) -> bool:
    if not from_user:
        return False
    user_id = int(getattr(from_user, "id", 0) or 0)
    if user_id in set(settings.admin_ids or []):
        return True
    username = (getattr(from_user, "username", "") or "").strip().lstrip("@").lower()
    return bool(username and username in set(settings.admin_usernames or []))


def _status_value(status: Any) -> str:
    return str(getattr(status, "value", status)).lower()


def _is_member_status(member: Any) -> bool:
    status = _status_value(getattr(member, "status", ""))
    if status in {ChatMemberStatus.LEFT.value, ChatMemberStatus.KICKED.value, "left", "kicked"}:
        return False
    if status == ChatMemberStatus.RESTRICTED.value and getattr(member, "is_member", True) is False:
        return False
    return True


async def _membership_cache_get(cache_key: tuple[int, str]) -> bool | None:
    ttl = max(0, int(settings.force_join_check_ttl or 0))
    if not ttl:
        return None
    client = await get_redis()
    redis_key = f"forcejoin:{cache_key[0]}:{cache_key[1]}"
    if client is not None:
        try:
            value = await client.get(redis_key)
            if value is None:
                return None
            return value == "1"
        except Exception as exc:
            logger.debug("Force-join Redis cache read failed: %s", exc, exc_info=True)
    cached = _MEMBERSHIP_CACHE.get(cache_key)
    now = time.monotonic()
    if cached and cached[0] > now:
        return cached[1]
    return None


async def _membership_cache_set(cache_key: tuple[int, str], value: bool) -> None:
    ttl = max(0, int(settings.force_join_check_ttl or 0))
    if not ttl:
        return
    client = await get_redis()
    redis_key = f"forcejoin:{cache_key[0]}:{cache_key[1]}"
    if client is not None:
        try:
            await client.setex(redis_key, ttl, "1" if value else "0")
            return
        except Exception as exc:
            logger.debug("Force-join Redis cache write failed: %s", exc, exc_info=True)
    _MEMBERSHIP_CACHE[cache_key] = (time.monotonic() + ttl, value)


async def _membership_cache_delete(cache_key: tuple[int, str]) -> None:
    client = await get_redis()
    redis_key = f"forcejoin:{cache_key[0]}:{cache_key[1]}"
    if client is not None:
        try:
            await client.delete(redis_key)
        except Exception as exc:
            logger.debug("Force-join Redis cache delete failed: %s", exc, exc_info=True)
    _MEMBERSHIP_CACHE.pop(cache_key, None)


def _start_watch_code_from_message(message: Message) -> str:
    text = (message.text or "").strip()
    if not text.startswith("/start"):
        return ""
    parts = text.split(maxsplit=1)
    return normalize_watch_start_arg(parts[1]) if len(parts) > 1 else ""


async def is_member_of_required_chat(bot: Bot, user_id: int, chat: RequiredChat, *, bypass_cache: bool = False) -> bool:
    cache_key = (int(user_id), str(chat.chat_id))
    if not bypass_cache:
        cached = await _membership_cache_get(cache_key)
        if cached is not None:
            return cached

    try:
        member = await bot.get_chat_member(chat_id=chat.chat_id, user_id=user_id)
        ok = _is_member_status(member)
        if ok:
            await _membership_cache_set(cache_key, True)
        else:
            await _membership_cache_delete(cache_key)
        return ok
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        logger.warning("Cannot verify FORCE_JOIN chat %s for user %s: %s", chat.chat_id, user_id, exc)
        if settings.force_join_fail_open:
            return True
        return False


async def missing_required_chats(bot: Bot, user_id: int, *, bypass_cache: bool = False) -> list[RequiredChat]:
    missing: list[RequiredChat] = []
    for chat in required_chats():
        if not await is_member_of_required_chat(bot, user_id, chat, bypass_cache=bypass_cache):
            missing.append(chat)
    return missing


def force_join_keyboard(chats: list[RequiredChat], lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    open_label = t("force_join_open", lang)
    for chat in chats:
        title = chat.title or str(chat.chat_id)
        if chat.url:
            rows.append([InlineKeyboardButton(text=f"{open_label}: {title}", url=chat.url)])
    rows.append([InlineKeyboardButton(text=t("force_join_check", lang), callback_data=FORCE_JOIN_CHECK_CALLBACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_force_join_prompt(message: Message, user: User, chats: list[RequiredChat]) -> None:
    lang = user.preferred_language if user.onboarded else settings.default_language
    await message.answer(t("force_join_required", lang), reply_markup=force_join_keyboard(chats, lang))


def _event_chat(event: Any) -> Any:
    if isinstance(event, Message):
        return event.chat
    if isinstance(event, CallbackQuery) and event.message:
        return getattr(event.message, "chat", None)
    chat = getattr(event, "chat", None)
    if chat is not None:
        return chat
    message = getattr(event, "message", None)
    return getattr(message, "chat", None) if message is not None else None


def _event_chat_is_private(event: Any) -> bool:
    chat = _event_chat(event)
    return bool(chat and getattr(chat, "type", None) == "private")


class ForceJoinMiddleware(BaseMiddleware):
    """Blocks private bot usage until the user joins configured channels/groups."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)
        chats = required_chats()
        if not chats or not _event_chat_is_private(event):
            return await handler(event, data)

        from_user = event.from_user
        if not from_user:
            return await handler(event, data)
        if is_force_join_exempt_user(from_user):
            return await handler(event, data)

        bot: Bot = data.get("bot") or event.bot
        async with SessionLocal() as session:
            user = await get_or_create_user(session, from_user)
            if isinstance(event, Message):
                watch_code = _start_watch_code_from_message(event)
                if watch_code:
                    await save_pending_watch_intent(session, int(from_user.id), watch_code)
            onboarded = bool(user.onboarded)
            lang = user.preferred_language if onboarded else settings.default_language
            is_check_callback = isinstance(event, CallbackQuery) and event.data == FORCE_JOIN_CHECK_CALLBACK
            # Strict mode verifies on every private update, so users who leave a required
            # channel/group are blocked again on their next message/button press.
            bypass_cache = bool(settings.force_join_strict or is_check_callback)
            missing = await missing_required_chats(bot, int(from_user.id), bypass_cache=bypass_cache)

        if not missing:
            if isinstance(event, CallbackQuery) and event.data == FORCE_JOIN_CHECK_CALLBACK:
                await event.answer(t("force_join_ok", lang), show_alert=True)
                if isinstance(event.message, Message):
                    try:
                        await event.message.edit_text(t("force_join_ok_message", lang), reply_markup=None)
                    except Exception as exc:
                        logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
                    if onboarded:
                        await event.message.answer(t("menu", lang), reply_markup=menu_kb(lang))
                    else:
                        state = data.get("state")
                        if state:
                            await state.set_state(Onboarding.language)
                        await event.message.answer(t("welcome_all", lang), reply_markup=language_kb())
                return None
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer(t("force_join_not_ready", lang), show_alert=True)
            if isinstance(event.message, Message):
                try:
                    # Keep the join screen clean: after every check, remove already-joined
                    # chats from the buttons and show only the missing channels/groups.
                    await event.message.edit_text(
                        t("force_join_required", lang),
                        reply_markup=force_join_keyboard(missing, lang),
                    )
                except Exception as exc:
                    logger.debug("Force-join prompt edit failed, sending fresh prompt: %s", exc, exc_info=True)
                    try:
                        await event.message.answer(t("force_join_required", lang), reply_markup=force_join_keyboard(missing, lang))
                    except Exception as send_exc:
                        logger.debug("Suppressed Telegram/bot operation failure: %s", send_exc, exc_info=True)
            return None

        await send_force_join_prompt(event, user, missing)
        return None

class PrivateChatOnlyMiddleware(BaseMiddleware):
    """Keep this bot as a private-chat product, even when it is admin in required groups.

    Required channels/groups are only used for membership checks. Normal bot buttons,
    matching, rooms and admin flows must not run inside those groups, otherwise the
    required group starts looking like the bot itself.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, (Message, CallbackQuery)) and _event_chat(event) is None:
            return await handler(event, data)
        if _event_chat_is_private(event):
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            try:
                await event.answer(t("private_chat_only", settings.default_language), show_alert=False)
            except Exception as exc:
                logger.debug("Suppressed non-private callback answer failure: %s", exc, exc_info=True)
        return None

