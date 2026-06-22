from __future__ import annotations

import asyncio
import html
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNetworkError
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, ErrorEvent
from sqlalchemy import func, select, text

from app.config import get_settings
from app.db import SessionLocal, init_db, db_health, close_db
from app.logging_config import configure_logging
from app.redis_cache import redis_health, close_redis
from app.keyboards import (
    cancel_kb,
    chat_kb,
    language_kb,
    menu_kb,
    mood_kb,
    movie_offer_kb,
    name_kb,
    profile_kb,
    report_kb,
    room_kb,
    room_movie_vote_kb,
    room_report_members_kb,
    public_room_list_kb,
    room_title_kb,
    room_type_kb,
    rooms_kb,
    host_controls_kb,
    admin_movie_code_kb,
    admin_skip_kb,
    premium_buy_kb,
    premium_upgrade_kb,
    admin_panel_kb,
    clean_confirm_kb,
    remove_kb,
    rules_kb,
    waiting_kb,
)
from app.models import AdCampaign, BanHistory, Block, Match, Movie, Payment, Report, Room, RoomMember, User
from app.moderation import check_message
from app.services import (
    cancel_waiting_db,
    create_block,
    create_match,
    create_movie_offer,
    create_report,
    create_room_report,
    end_match,
    add_warning,
    create_ad_campaign,
    get_active_ad,
    is_telegram_restricted,
    restriction_remaining_text,
    reserve_anon_name,
    should_show_ad_now,
    mark_bot_blocked,
    ban_user,
    unban_user,
    mute_user,
    unmute_user,
    is_user_muted,
    muted_remaining_text,
    get_ban_history,
    get_recent_match_messages,
    format_recent_messages,
    review_report,
    get_active_match,
    get_movie,
    get_movie_by_id,
    get_offer,
    get_active_room,
    create_room,
    find_public_room,
    list_public_rooms,
    join_room,
    leave_room,
    close_inactive_rooms,
    create_room_movie_offer,
    get_room_by_invite,
    get_room_member,
    get_room_offer,
    is_room_host,
    kick_room_member,
    set_room_member_mute,
    vote_room_movie_offer,
    get_room_users,
    get_room_members,
    grant_plan,
    can_skip_today,
    record_skip,
    can_unlock_movie,
    consume_movie_unlock,
    refund_movie_unlock,
    record_movie_unlock,
    is_waiting,
    waiting_count,
    can_join_rooms,
    can_join_private_rooms,
    can_edit_name_after_onboarding,
    usage_summary,
    star_price,
    create_payment_invoice,
    get_payment_by_payload,
    complete_payment,
    normalize_watch_start_arg,
    save_pending_watch_intent,
    pop_pending_watch_intent,
    mock_activate_plan,
    create_admin_movie,
    update_movie_status,
    edit_movie_field,
    get_movie_any,
    list_movies,
    get_movie_by_number,
    format_numbered_movies,
    movie_admin_summary,
    channel_post_template,
    generate_movie_code,
    delete_movie,
    delete_user_everything,
    save_room_chat,
    get_or_create_user,
    get_other_user,
    get_user_by_id,
    get_user_by_telegram,
    save_chat,
    start_waiting,
    prune_waiting,
    update_anon_name,
    update_chat_mood,
    update_language,
)
from app.states import ChatStates, Onboarding, RoomStates, AdminMovieStates, AdminAdStates
from app.force_join import ForceJoinMiddleware, PrivateChatOnlyMiddleware, validate_force_join_configuration
from app.texts import action_from_text, lang_name, mood_from_text, mood_label, report_label, t, validate_texts
from app.utils import has_contact_info, make_anon_name, movie_card, valid_anon_name

settings = get_settings()
logger = logging.getLogger(__name__)
router = Router()


def mock_payments_enabled() -> bool:
    return bool(settings.mock_payments and not settings.is_production)


def movie_codes_channel_url() -> str:
    url = (settings.movies_channel_url or "").strip()
    if not url and (settings.movies_channel_username or "").strip():
        username = settings.movies_channel_username.strip().lstrip("@")
        url = f"https://t.me/{username}"
    return url


def movie_code_prompt(key: str, lang: str) -> str:
    text = t(key, lang)
    url = movie_codes_channel_url()
    if not url:
        return text
    extra = {
        "uz": "🎬 Kino kodlari kanali:\n{url}\n\nKodni kanaldan olib, shu yerga yuboring.",
        "ru": "🎬 Канал с кодами фильмов:\n{url}\n\nВозьмите код из канала и отправьте его сюда.",
        "en": "🎬 Movie codes channel:\n{url}\n\nTake a code from the channel and send it here.",
    }.get(lang, "🎬 Movie codes channel:\n{url}\n\nTake a code from the channel and send it here.")
    return f"{text}\n\n{extra.format(url=html.escape(url))}"


async def answer_with_retry(message: Message, text: str, **kwargs):
    last_exc = None
    for attempt in range(2):
        try:
            return await message.answer(text, **kwargs)
        except TelegramNetworkError as exc:
            last_exc = exc
            logger.warning("Telegram network error while sending answer, retry=%s: %s", attempt + 1, exc)
            await asyncio.sleep(0.7)
    logger.warning("Telegram answer failed after retry: %s", last_exc, exc_info=True)
    return None


@router.errors()
async def telegram_network_error_handler(event: ErrorEvent) -> bool:
    if isinstance(event.exception, TelegramNetworkError):
        logger.warning("Suppressed transient Telegram network error: %s", event.exception, exc_info=True)
        return True
    return False


# v19: plan-based content permissions for anonymous chats and rooms.
# Free: text/emojis + photos only.
# Plus: text/photos/stickers/GIFs/audio/voice, but no videos/circle videos/documents.
# Pro/Admin: any Telegram message type, and links/contact data are allowed.
FREE_ALLOWED_KINDS = {"text", "photo"}
PLUS_ALLOWED_KINDS = {"text", "photo", "sticker", "animation", "audio", "voice"}
PRO_ALLOWED_KINDS = {"text", "photo", "sticker", "animation", "audio", "voice", "video", "video_note", "document", "video_document", "other"}


def plan_rank_name(user: User) -> str:
    return "pro" if user.is_admin else (user.plan or "free")


def message_kind(message: Message) -> str:
    if message.text:
        return "text"
    if message.photo:
        return "photo"
    if message.sticker:
        return "sticker"
    if message.animation:
        return "animation"
    if message.audio:
        return "audio"
    if message.voice:
        return "voice"
    if message.video_note:
        return "video_note"
    if message.video:
        return "video"
    if message.document:
        mime = (message.document.mime_type or "").lower()
        if mime.startswith("video/"):
            return "video_document"
        return "document"
    return "other"


def media_allowed_for_user(user: User, kind: str) -> bool:
    if user.is_admin or user.plan == "pro":
        return True
    if user.plan == "plus":
        return kind in PLUS_ALLOWED_KINDS
    return kind in FREE_ALLOWED_KINDS


def moderate_text_for_plan(user: User, text: str):
    # Anonymous safety rule: paid users may unlock richer media, but links,
    # usernames and phone/contact data stay blocked until a future mutual-consent
    # contact exchange flow exists.
    return check_message(text or "")


def media_kind_label(kind: str, lang: str) -> str:
    key = "media_" + ("video" if kind == "video_document" else kind)
    try:
        return t(key, lang)
    except KeyError:
        return t("media_other", lang)



def choice_to_lang(text: str | None) -> str | None:
    return {"O‘zbekcha": "uz", "Русский": "ru", "English": "en"}.get((text or "").strip())


def admin_username_allowed(tg_user) -> bool:
    return int(getattr(tg_user, "id", 0)) in set(settings.admin_ids or [])


def admin_is_authed(tg_user) -> bool:
    return admin_username_allowed(tg_user)


async def require_admin(message: Message, session, user: User, *, prompt: bool = True) -> bool:
    lang = user.preferred_language
    if not user.is_admin and admin_username_allowed(message.from_user):
        user.is_admin = True
        await session.commit()
    if user.is_admin:
        return True
    if prompt:
        await message.answer(t("admin_denied", lang))
    return False


async def admin_stats_text(session, lang: str) -> str:
    now = datetime.utcnow()
    users = (await session.execute(select(func.count(User.id)))).scalar_one()
    movies = (await session.execute(select(func.count(Movie.id)))).scalar_one()
    active = (await session.execute(select(func.count(Match.id)).where(Match.status == "active"))).scalar_one()
    reports = (await session.execute(select(func.count(Report.id)).where(Report.status == "open"))).scalar_one()
    blocks = (await session.execute(select(func.count(Block.id)))).scalar_one()
    rooms = (await session.execute(select(func.count(Room.id)).where(Room.status == "open"))).scalar_one()
    muted = (await session.execute(select(func.count(User.id)).where(User.muted_until.is_not(None)))).scalar_one()
    low_trust = (await session.execute(select(func.count(User.id)).where(User.trust_score < 50))).scalar_one()
    plus_active = (await session.execute(
        select(func.count(User.id)).where(User.plan == "plus", User.plan_expires_at > now)
    )).scalar_one()
    pro_active = (await session.execute(
        select(func.count(User.id)).where(User.plan == "pro", User.plan_expires_at > now)
    )).scalar_one()
    stars_today = (await session.execute(
        select(func.coalesce(func.sum(Payment.stars_amount), 0)).where(
            Payment.status == "succeeded",
            Payment.updated_at >= now.replace(hour=0, minute=0, second=0, microsecond=0),
        )
    )).scalar_one()
    waiting = await waiting_count(session)
    return t("admin_stats_text", lang).format(
        users=users, movies=movies, active=active, rooms=rooms, waiting=waiting,
        reports=reports, blocks=blocks, muted=muted, low_trust=low_trust,
        plus_active=plus_active, pro_active=pro_active, stars_today=stars_today,
    )


async def safe_delete(bot: Bot, chat_id: int, message_id: int | None) -> None:
    if not settings.delete_cleanup_messages or not message_id:
        return
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as exc:
        logger.debug("Could not delete message chat_id=%s message_id=%s: %s", chat_id, message_id, exc)


async def safe_send_to_user(bot: Bot, recipient: User, text: str, *, reply_markup=None, parse_mode: ParseMode | None = None) -> bool:
    """Send a message without letting blocked/deleted chats break matchmaking.

    Returns False when Telegram says the bot cannot message the user. The caller
    can then end the match and keep the other user usable for new partners.
    """
    try:
        await bot.send_message(
            recipient.telegram_id,
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
        return True
    except TelegramForbiddenError:
        mark_bot_blocked(recipient.telegram_id, recipient.id)
        logger.info("User %s blocked the bot; removed from matching state", recipient.telegram_id)
        return False
    except TelegramBadRequest as exc:
        msg = str(exc).lower()
        if "bot was blocked" in msg or "chat not found" in msg or "user is deactivated" in msg:
            mark_bot_blocked(recipient.telegram_id, recipient.id)
            logger.info("User %s cannot receive bot messages: %s", recipient.telegram_id, exc)
            return False
        raise


async def safe_copy_to_user(bot: Bot, recipient: User, from_chat_id: int, message_id: int) -> bool:
    try:
        await bot.copy_message(recipient.telegram_id, from_chat_id, message_id)
        return True
    except TelegramForbiddenError:
        mark_bot_blocked(recipient.telegram_id, recipient.id)
        logger.info("User %s blocked the bot during copy_message", recipient.telegram_id)
        return False
    except TelegramBadRequest as exc:
        msg = str(exc).lower()
        if "bot was blocked" in msg or "chat not found" in msg or "user is deactivated" in msg:
            mark_bot_blocked(recipient.telegram_id, recipient.id)
            logger.info("User %s cannot receive copied messages: %s", recipient.telegram_id, exc)
            return False
        return False


async def send_admins(bot: Bot, text: str) -> None:
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception as exc:
            logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)


async def require_user(message: Message) -> User | None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        active, restriction = await is_telegram_restricted(session, user.telegram_id)
        if active and not user.is_admin:
            await message.answer(t("banned_until", user.preferred_language).format(time=restriction_remaining_text(restriction)))
            return None
        if user.is_banned and not user.is_admin:
            await message.answer(t("banned", user.preferred_language))
            return None
        return user




def fresh_start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 START / BOSHLASH / НАЧАТЬ", callback_data="fresh_start")]])


async def delete_recent_chat_window(bot: Bot, chat_id: int, from_message_id: int | None, *, limit: int | None = None) -> int:
    """Fast best-effort private-chat cleanup.

    Telegram bots do not have a real "clear whole chat history" method. When the
    Bot API/client supports bulk deletion we use it; otherwise we fire deletes in
    concurrent batches so the user does not watch a slow one-by-one animation.
    """
    if not settings.delete_cleanup_messages or not from_message_id:
        return 0
    max_window = int(limit if limit is not None else settings.clean_delete_window)
    start = int(from_message_id)
    stop = max(1, start - max_window + 1)
    ids = list(range(stop, start + 1))
    deleted = 0

    async def delete_one(mid: int) -> int:
        try:
            await bot.delete_message(chat_id, mid)
            return 1
        except Exception as exc:
            logger.debug("Could not delete cleanup message chat_id=%s message_id=%s: %s", chat_id, mid, exc)
            return 0

    # Prefer Telegram Bot API bulk deletion when the installed aiogram exposes it.
    bulk = getattr(bot, "delete_messages", None)
    if callable(bulk):
        for i in range(0, len(ids), 100):
            chunk = ids[i:i + 100]
            try:
                await bulk(chat_id=chat_id, message_ids=chunk)
                deleted += len(chunk)
            except Exception as exc:
                logger.debug("Bulk cleanup delete failed chat_id=%s chunk=%s: %s", chat_id, len(chunk), exc)
                # Fallback only for this chunk.
                results = await asyncio.gather(*(delete_one(mid) for mid in chunk), return_exceptions=True)
                deleted += sum(int(r) for r in results if isinstance(r, int))
        return deleted

    # Older aiogram versions: concurrent deletion, still much faster than a visible loop.
    for i in range(0, len(ids), 60):
        chunk = ids[i:i + 60]
        results = await asyncio.gather(*(delete_one(mid) for mid in chunk), return_exceptions=True)
        deleted += sum(int(r) for r in results if isinstance(r, int))
    return deleted


async def perform_clean_reset(message: Message, state: FSMContext) -> None:
    chat_id = message.chat.id
    lang = settings.default_language
    temp_id = message.message_id
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        await delete_user_everything(session, user)
    await state.clear()

    # Remove the custom keyboard immediately. This message is also deleted in the
    # same fast cleanup window so the final screen feels like Telegram's fresh START state.
    try:
        temp = await message.bot.send_message(chat_id, t("clean_fast_started", lang), reply_markup=remove_kb())
        temp_id = max(temp_id, temp.message_id)
    except Exception as exc:
        logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)

    deleted = await delete_recent_chat_window(message.bot, chat_id, temp_id)

    # Default is no final bot message: if Telegram lets us delete the visible window,
    # the chat returns to the clean START-like screen. Enable CLEAN_FINAL_MESSAGE=true
    # only for platforms where a fallback Start card is preferred.
    if settings.clean_final_message or deleted == 0:
        await message.bot.send_message(chat_id, t("clean_fallback", lang), reply_markup=fresh_start_kb())


async def handle_admin_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        if not admin_username_allowed(message.from_user):
            await message.answer(t("admin_denied", lang))
            return
        user.is_admin = True
        user.onboarded = True
        await session.commit()
        await message.answer(t("admin_menu", lang), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))


@router.message(Command("admin"))
async def cmd_admin_priority(message: Message, state: FSMContext) -> None:
    await handle_admin_entry(message, state)


@router.message(Command("clean"))
async def cmd_clean_priority(message: Message, state: FSMContext) -> None:
    await perform_clean_reset(message, state)


@router.callback_query(F.data == "fresh_start")
async def fresh_start_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    async with SessionLocal() as session:
        user = await get_or_create_user(session, callback.from_user)
        lang = user.preferred_language
        if admin_username_allowed(callback.from_user):
            user.is_admin = True
            user.onboarded = True
            await session.commit()
            await callback.message.answer(t("admin_menu", lang), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))
            await callback.answer()
            return
    await state.set_state(Onboarding.language)
    await callback.message.answer(t("welcome_all", "uz"), reply_markup=language_kb())
    await callback.answer()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, command: CommandObject | None = None) -> None:
    try:
        await message.bot.send_message(message.chat.id, "✅ /start handler reached.")
    except Exception as exc:
        logger.exception("TEMP start debug send failed: %s", exc)

    try:
        await state.clear()
        await message.bot.send_message(message.chat.id, "✅ state.clear passed.")
    except Exception as exc:
        logger.exception("TEMP state.clear failed: %s", exc)
        await message.bot.send_message(message.chat.id, f"❌ state.clear failed: {type(exc).__name__}: {exc}")
        return
    start_arg = (command.args if command else None) or ""
    watch_code = normalize_watch_start_arg(start_arg) if start_arg else ""
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        if admin_username_allowed(message.from_user):
            user.is_admin = True
            user.onboarded = True
            await session.commit()
            await message.answer(t("admin_menu", lang), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))
            return
        active_restriction, restriction = await is_telegram_restricted(session, user.telegram_id)
        if active_restriction and not user.is_admin:
            await message.answer(t("banned_until", lang).format(time=restriction_remaining_text(restriction)))
            return
        if user.is_banned and not user.is_admin:
            await message.answer(t("banned", lang))
            return
        if user.onboarded:
            if watch_code:
                await offer_movie_to_active_context(message, session, user, watch_code)
                return
            match = await get_active_match(session, user.id)
            if match:
                await message.answer(t("chat_help", lang), reply_markup=chat_kb(lang))
            else:
                await message.answer(t("menu", lang), reply_markup=menu_kb(lang))
            return
    if watch_code:
        async with SessionLocal() as session:
            await save_pending_watch_intent(session, int(message.from_user.id), watch_code)
    await state.set_state(Onboarding.language)
    await message.answer(t("welcome_all", lang), reply_markup=language_kb())


@router.message(Onboarding.language)
async def onboarding_language(message: Message, state: FSMContext) -> None:
    lang = choice_to_lang(message.text)
    if not lang:
        await message.answer(t("welcome_all", "uz"), reply_markup=language_kb())
        return
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        await update_language(session, user, lang)
    await state.set_state(Onboarding.rules)
    await message.answer(t("rules_after_lang", lang), reply_markup=rules_kb(lang))


@router.message(Onboarding.rules)
async def onboarding_rules(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
    if action_from_text(message.text or "") != "agree":
        await message.answer(t("rules_after_lang", lang), reply_markup=rules_kb(lang))
        return
    await state.set_state(Onboarding.anon_name)
    await message.answer(t("choose_name", lang), reply_markup=name_kb(lang))


@router.message(Onboarding.anon_name)
async def onboarding_name(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        action = action_from_text(message.text or "")
        if action == "auto_name":
            name = await reserve_anon_name(session, user)
        else:
            name = (message.text or "").strip()
            if not valid_anon_name(name):
                await message.answer(t("bad_name", lang), reply_markup=name_kb(lang))
                return
            await update_anon_name(session, user, name)
    await state.set_state(Onboarding.chat_mood)
    await message.answer(t("choose_mood", lang), reply_markup=mood_kb(lang))


@router.message(Onboarding.chat_mood)
async def onboarding_mood(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        mood = mood_from_text(message.text)
        if not mood:
            await message.answer(t("invalid_mood", lang), reply_markup=mood_kb(lang))
            return
        await update_chat_mood(session, user, mood)
        user.onboarded = True
        await session.commit()
    await state.clear()
    async with SessionLocal() as session:
        pending_code = await pop_pending_watch_intent(session, int(message.from_user.id))
    if pending_code:
        async with SessionLocal() as session:
            fresh_user = await get_or_create_user(session, message.from_user)
            await message.answer(t("profile_done", lang), reply_markup=menu_kb(lang))
            await send_movie_to_user(message, session, fresh_user, pending_code)
    else:
        await message.answer(t("profile_done", lang), reply_markup=menu_kb(lang))


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await require_user(message)
    if not user:
        return
    if user.is_admin:
        await message.answer(t("admin_menu", user.preferred_language), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(user.preferred_language))
        return
    await message.answer(t("menu", user.preferred_language), reply_markup=menu_kb(user.preferred_language))


@router.message(Command("premium"))
async def cmd_premium(message: Message) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        active, restriction = await is_telegram_restricted(session, user.telegram_id)
        if active and not user.is_admin:
            await message.answer(t("banned_until", user.preferred_language).format(time=restriction_remaining_text(restriction)))
            return
        if user.is_banned and not user.is_admin:
            await message.answer(t("banned", user.preferred_language))
            return
        if user.is_admin:
            await message.answer(t("admin_menu", user.preferred_language), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(user.preferred_language))
            return
        await premium_flow(message, session, user)


@router.message(Command("paysupport"))
async def cmd_pay_support(message: Message) -> None:
    user = await require_user(message)
    if not user:
        return
    await message.answer(t("paysupport", user.preferred_language), reply_markup=menu_kb(user.preferred_language))


async def deliver_movie(bot: Bot, chat_id: int, movie: Movie, lang: str, reply_markup=None) -> None:
    media_id = (movie.video_file_id or "").strip()
    if media_id.lower().startswith("doc:"):
        await bot.send_document(chat_id, media_id[4:], reply_markup=reply_markup)
    elif media_id:
        await bot.send_video(chat_id, media_id, reply_markup=reply_markup)
    elif movie.legal_watch_url:
        await bot.send_message(chat_id, t("watch_alone_sent", lang) + f"\n▶️ {html.escape(movie.legal_watch_url)}", reply_markup=reply_markup)
    else:
        raise RuntimeError("movie_has_no_deliverable_source")


async def safe_deliver_movie(bot: Bot, chat_id: int, movie: Movie, lang: str, reply_markup=None, *, user_id: int | None = None) -> bool:
    """Deliver a movie without leaking raw Telegram file IDs to users.

    Returns True when the user received either Telegram media or a legal URL
    fallback. Returns False only when no useful delivery path exists.
    """
    try:
        await deliver_movie(bot, chat_id, movie, lang, reply_markup=reply_markup)
        return True
    except Exception as exc:
        logger.warning(
            "Movie delivery failed movie_id=%s user_id=%s chat_id=%s: %s",
            movie.id, user_id, chat_id, exc, exc_info=True,
        )
        if movie.legal_watch_url:
            try:
                await bot.send_message(
                    chat_id,
                    t("watch_alone_sent", lang) + f"\n▶️ {html.escape(movie.legal_watch_url)}",
                    reply_markup=reply_markup,
                )
                return True
            except Exception as fallback_exc:
                logger.warning(
                    "Movie legal URL fallback failed movie_id=%s user_id=%s chat_id=%s: %s",
                    movie.id, user_id, chat_id, fallback_exc, exc_info=True,
                )
        try:
            await bot.send_message(chat_id, t("movie_temporarily_unavailable", lang), reply_markup=reply_markup)
        except Exception as notify_exc:
            logger.debug("Movie unavailable notification failed: %s", notify_exc, exc_info=True)
        return False


async def send_movie_to_user(message: Message, session, user: User, code: str) -> bool:
    lang = user.preferred_language
    movie = await get_movie(session, code)
    if not movie:
        await message.answer(t("movie_not_found", lang), reply_markup=menu_kb(lang))
        return False
    ok, used, limit, period = await consume_movie_unlock(session, user)
    if not ok:
        await message.answer(t("movie_limit", lang).format(used=used, limit=limit, period=period), reply_markup=menu_kb(lang))
        await send_upgrade_prompt(message, user, "upgrade_movie_limit")
        return False
    delivered = await safe_deliver_movie(message.bot, message.chat.id, movie, lang, reply_markup=menu_kb(lang), user_id=user.id)
    if not delivered:
        await refund_movie_unlock(session, user)
        return False
    return True


async def offer_movie_to_active_context(message: Message, session, user: User, code: str) -> bool:
    """Use movie deep-links correctly during active chat/room.

    A user who taps a channel movie link while already in a 1-1 chat should
    create a normal approval offer for the partner instead of receiving the
    movie alone. Idle users still receive the movie directly.
    """
    lang = user.preferred_language
    movie = await get_movie(session, code)
    if not movie:
        await message.answer(t("movie_not_found", lang), reply_markup=chat_kb(lang))
        return False

    match = await get_active_match(session, user.id)
    if match:
        other = await get_other_user(session, match, user.id)
        if not other:
            await message.answer(t("partner_unavailable", lang), reply_markup=chat_kb(lang))
            return False
        offer = await create_movie_offer(session, match, user.id, movie)
        other_lang = other.preferred_language
        await message.answer(t("offer_sent", lang), reply_markup=chat_kb(lang))
        try:
            await message.bot.send_message(
                other.telegram_id,
                f"{t('offer_received', other_lang)}\n\n{movie_card(movie, other_lang)}",
                reply_markup=movie_offer_kb(offer.id, other_lang),
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            logger.warning("Failed to send deep-link movie offer: %s", exc, exc_info=True)
        return True

    room = await get_active_room(session, user.id)
    if room:
        member = await get_room_member(session, room.id, user.id)
        if member and member.is_muted:
            await message.answer(t("you_are_muted", lang), reply_markup=room_kb(lang))
            return False
        offer = await create_room_movie_offer(session, room, user, movie)
        users = await get_room_users(session, room.id)
        for member_user in users:
            try:
                ml = member_user.preferred_language
                await message.bot.send_message(
                    member_user.telegram_id,
                    f"{t('room_offer_started', ml)}\n\n{movie_card(movie, ml)}\n\n{t('room_vote_result', ml).format(yes=offer.yes_votes_count, no=offer.no_votes_count, total=len(users))}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=room_movie_vote_kb(offer.id, ml),
                )
            except Exception as exc:
                logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
        return True

    return await send_movie_to_user(message, session, user, code)


@router.message(Command("stats"))
@router.message(Command("admin_stats"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        command_name = (message.text or "").split()[0].lstrip("/").split("@")[0]


        if not await require_admin(message, session, user):
            return

        if command_name in {"stats", "admin_stats"}:
            await message.answer(await admin_stats_text(session, lang), reply_markup=admin_panel_kb(lang))
        else:
            await message.answer(t("admin_menu", lang), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))




# ---------------- v13 movie admin publishing ----------------
@router.message(Command("admin_movies"))
async def cmd_admin_movies(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            return
        status = (command.args or "").strip().lower() or None
        if status not in {"draft", "published", "hidden", None}:
            await message.answer(t("admin_usage_movies", lang), reply_markup=admin_panel_kb(lang))
            return
        movies = await list_movies(session, status=status, limit=500)
    if not movies:
        await message.answer(t("admin_movie_list_empty", lang), reply_markup=admin_panel_kb(lang))
        return
    lines = [t("admin_movie_list_header", lang)]
    for i, m in enumerate(movies, 1):
        lines.append(f"{i}. <code>{html.escape(m.code)}</code> — {html.escape(m.title)} [{html.escape(m.status)}]")
    lines.append(t("admin_movie_list_footer", lang))
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))


@router.message(Command("admin_movie"))
async def cmd_admin_movie(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        code = (command.args or "").strip()
        if not code:
            await message.answer(t("admin_usage_movie", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        movie = await get_movie_any(session, code)
        if not movie:
            await message.answer(t("admin_movie_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        text = movie_admin_summary(movie)
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("admin_generate_code"))
async def cmd_admin_generate_code(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        prefix = (command.args or "KINO").strip() or "KINO"
        code = await generate_movie_code(session, prefix)
    await message.answer(t("admin_generated_code", admin.preferred_language).format(code=code), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(admin.preferred_language))


@router.message(Command("admin_add_movie"))
async def cmd_admin_add_movie(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        lang = admin.preferred_language
    await state.clear()
    await state.set_state(AdminMovieStates.code)
    await message.answer(t("admin_add_movie_start", lang), reply_markup=admin_movie_code_kb(lang), parse_mode=ParseMode.HTML)


@router.message(AdminMovieStates.code)
async def admin_movie_code_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            await state.clear()
            return
        if action_from_text(message.text or "") == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=admin_panel_kb(lang))
            return
        raw = (message.text or "").strip().upper()
        if not raw or raw == "AUTO":
            code = await generate_movie_code(session, "KINO")
        else:
            from app.services import normalize_movie_code
            code = normalize_movie_code(raw)
            if await get_movie_any(session, code):
                await message.answer(t("admin_duplicate_code", lang), reply_markup=admin_movie_code_kb(lang))
                return
    await state.update_data(code=code)
    await state.set_state(AdminMovieStates.title)
    await message.answer(t("admin_movie_title_prompt", lang), reply_markup=cancel_kb(lang), parse_mode=ParseMode.HTML)


@router.message(AdminMovieStates.title)
async def admin_movie_title_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            await state.clear()
            return
    if action_from_text(message.text or "") == "cancel":
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=admin_panel_kb(lang))
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer(t("admin_movie_title_prompt", lang), reply_markup=cancel_kb(lang), parse_mode=ParseMode.HTML)
        return
    await state.update_data(title=title)
    await state.set_state(AdminMovieStates.movie_type)
    await answer_with_retry(message, t("admin_movie_type_prompt", lang), reply_markup=cancel_kb(lang), parse_mode=ParseMode.HTML)


@router.message(AdminMovieStates.movie_type)
async def admin_movie_type_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            await state.clear()
            return
    if action_from_text(message.text or "") == "cancel":
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=admin_panel_kb(lang))
        return
    movie_type = (message.text or "").strip() or "Movie"
    await state.update_data(movie_type=movie_type)
    await state.set_state(AdminMovieStates.language)
    await answer_with_retry(message, t("admin_movie_language_prompt", lang), reply_markup=cancel_kb(lang), parse_mode=ParseMode.HTML)


@router.message(AdminMovieStates.language)
async def admin_movie_language_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            await state.clear()
            return
    if action_from_text(message.text or "") == "cancel":
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=admin_panel_kb(lang))
        return
    movie_language = (message.text or "").strip().lower()[:32] or "uz"
    await state.update_data(movie_language=movie_language)
    await state.set_state(AdminMovieStates.year)
    await answer_with_retry(message, t("admin_movie_year_prompt", lang), reply_markup=cancel_kb(lang), parse_mode=ParseMode.HTML)


@router.message(AdminMovieStates.year)
async def admin_movie_year_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            await state.clear()
            return
    if action_from_text(message.text or "") == "cancel":
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=admin_panel_kb(lang))
        return
    raw_year = (message.text or "").strip()
    movie_year = None
    if raw_year and raw_year not in {"-", "—"}:
        try:
            movie_year = int(raw_year)
        except ValueError:
            await message.answer(t("admin_movie_invalid_year", lang), reply_markup=cancel_kb(lang))
            return
    await state.update_data(movie_year=movie_year)
    await state.set_state(AdminMovieStates.video)
    await answer_with_retry(message, t("admin_upload_video", lang), reply_markup=cancel_kb(lang), parse_mode=ParseMode.HTML)


@router.message(AdminMovieStates.video)
async def admin_movie_watch_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            await state.clear()
            return
        if action_from_text(message.text or "") == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=admin_panel_kb(lang))
            return

        data = await state.get_data()
        code = data.get("code") or await generate_movie_code(session, "KINO")
        title = (data.get("title") or f"Movie {code}").strip()
        movie_type = (data.get("movie_type") or "Movie").strip()
        movie_language = (data.get("movie_language") or "uz").strip().lower()[:32]
        movie_year = data.get("movie_year")
        description = (message.caption or "").strip()
        legal_url = ""
        video_file_id = ""
        source_type = "own_content"
        source_note = "Admin uploaded video via Telegram bot."

        text_value = (message.text or "").strip()
        if text_value.startswith(("http://", "https://")):
            legal_url = text_value
            source_type = "external_legal_link"
            source_note = "Admin provided external legal watch URL."
            description = ""
        elif message.video:
            video_file_id = message.video.file_id
        elif message.document and (message.document.mime_type or "").lower().startswith("video/"):
            video_file_id = "doc:" + message.document.file_id
            source_note = "Admin uploaded video document via Telegram bot."
        else:
            await message.answer(t("admin_video_only", lang), reply_markup=cancel_kb(lang))
            return

        try:
            movie = await create_admin_movie(
                session, admin,
                code=code,
                title=title,
                description=description,
                legal_watch_url=legal_url,
                video_file_id=video_file_id,
                source_type=source_type,
                source_note=source_note,
                year=movie_year,
                genres=movie_type,
                language=movie_language,
                status="published",
            )
        except ValueError:
            await message.answer(t("admin_duplicate_code", lang), reply_markup=admin_movie_code_kb(lang))
            await state.set_state(AdminMovieStates.code)
            return
        movies = await list_movies(session, status=None, limit=500)
        number = next((i for i, m in enumerate(movies, 1) if m.id == movie.id), len(movies))
    await state.clear()
    await message.answer(
        t("admin_simple_saved", lang).format(number=number, code=html.escape(movie.code), title=html.escape(movie.title)),
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel_kb(lang),
    )


@router.message(AdminMovieStates.delete_number)
async def admin_delete_movie_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            await state.clear()
            return
        if action_from_text(message.text or "") == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=admin_panel_kb(lang))
            return
        raw = (message.text or "").strip()
        if not raw.isdigit():
            movies = await list_movies(session, status=None, limit=500)
            await message.answer(t("admin_invalid_movie_number", lang) + "\n\n" + format_numbered_movies(movies), reply_markup=cancel_kb(lang))
            return
        movie = await get_movie_by_number(session, int(raw))
        if not movie:
            movies = await list_movies(session, status=None, limit=500)
            await message.answer(t("admin_invalid_movie_number", lang) + "\n\n" + format_numbered_movies(movies), reply_markup=cancel_kb(lang))
            return
        deleted_code = await delete_movie(session, movie)
    await state.clear()
    await message.answer(t("admin_movie_deleted", lang).format(code=html.escape(deleted_code)), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))


@router.message(AdminMovieStates.post_number)
async def admin_post_template_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            await state.clear()
            return
        if action_from_text(message.text or "") == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=admin_panel_kb(lang))
            return
        raw = (message.text or "").strip()
        movie = None
        if raw.isdigit():
            movie = await get_movie_by_number(session, int(raw))
        if not movie:
            movie = await get_movie_any(session, raw)
        if not movie:
            await message.answer(t("admin_invalid_movie_number", lang), reply_markup=admin_panel_kb(lang))
            await state.clear()
            return
        bot_info = await message.bot.get_me()
        text = channel_post_template(movie, bot_info.username)
    await state.clear()
    await message.answer(f"<pre>{html.escape(text)}</pre>", parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))


@router.message(Command("admin_publish_movie"))
async def cmd_admin_publish_movie(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            return
        code = (command.args or "").strip()
        if not code:
            await message.answer(t("admin_usage_publish", lang), reply_markup=admin_panel_kb(lang))
            return
        movie = await get_movie_any(session, code)
        if not movie:
            await message.answer(t("admin_movie_not_found", lang), reply_markup=admin_panel_kb(lang))
            return
        movie, errors = await update_movie_status(session, movie, "published")
    if errors:
        await message.answer(t("admin_cannot_publish", lang).format(errors=", ".join(errors)), reply_markup=admin_panel_kb(lang))
    else:
        await message.answer(t("admin_movie_published", lang).format(code=movie.code), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))


@router.message(Command("admin_hide_movie"))
async def cmd_admin_hide_movie(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            return
        code = (command.args or "").strip()
        if not code:
            await message.answer(t("admin_usage_publish", lang).replace("/admin_publish_movie", "/admin_hide_movie"), reply_markup=admin_panel_kb(lang))
            return
        movie = await get_movie_any(session, code)
        if not movie:
            await message.answer(t("admin_movie_not_found", lang), reply_markup=admin_panel_kb(lang))
            return
        movie, _ = await update_movie_status(session, movie, "hidden")
    await message.answer(t("admin_movie_hidden", lang).format(code=movie.code), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))


@router.message(Command("admin_draft_movie"))
async def cmd_admin_draft_movie(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            return
        code = (command.args or "").strip()
        if not code:
            await message.answer(t("admin_usage_publish", lang).replace("/admin_publish_movie", "/admin_draft_movie"), reply_markup=admin_panel_kb(lang))
            return
        movie = await get_movie_any(session, code)
        if not movie:
            await message.answer(t("admin_movie_not_found", lang), reply_markup=admin_panel_kb(lang))
            return
        movie, _ = await update_movie_status(session, movie, "draft")
    await message.answer(t("admin_movie_draft", lang).format(code=movie.code), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))


@router.message(Command("admin_edit_movie"))
async def cmd_admin_edit_movie(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            return
        raw = command.args or ""
        parts = raw.split(maxsplit=2)
        if len(parts) < 3:
            await message.answer(t("admin_edit_usage", lang), reply_markup=admin_panel_kb(lang))
            return
        code, field, value = parts
        movie = await get_movie_any(session, code)
        if not movie:
            await message.answer(t("admin_movie_not_found", lang), reply_markup=admin_panel_kb(lang))
            return
        movie, err = await edit_movie_field(session, movie, field, value)
    if err:
        await message.answer(t("admin_edit_failed", lang).format(error=err), reply_markup=admin_panel_kb(lang))
    else:
        await message.answer(t("admin_edit_done", lang).format(field=field, code=movie.code), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))


@router.message(Command("admin_delete_movie"))
async def cmd_admin_delete_movie(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            return
        raw = (command.args or "").strip()
        if not raw:
            movies = await list_movies(session, status=None, limit=500)
            if not movies:
                await message.answer(t("admin_movie_list_empty", lang), reply_markup=admin_panel_kb(lang))
                return
            await message.answer(t("admin_delete_choose_number", lang).format(movies=html.escape(format_numbered_movies(movies))), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))
            return
        movie = await get_movie_by_number(session, int(raw)) if raw.isdigit() else await get_movie_any(session, raw)
        if not movie:
            await message.answer(t("admin_movie_not_found", lang), reply_markup=admin_panel_kb(lang))
            return
        deleted_code = await delete_movie(session, movie)
    await message.answer(t("admin_movie_deleted", lang).format(code=html.escape(deleted_code)), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))


@router.message(Command("admin_post_template"))
async def cmd_admin_post_template(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        code = (command.args or "").strip()
        movie = await get_movie_any(session, code)
        if not movie:
            await message.answer(t("admin_post_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
    me = await message.bot.get_me()
    await message.answer("<pre>" + html.escape(channel_post_template(movie, me.username)) + "</pre>", parse_mode=ParseMode.HTML)
# ---------------- end v13 movie admin publishing ----------------


@router.message(Command("reports"))
@router.message(Command("admin_reports"))
async def cmd_admin_reports(message: Message) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, user):
            return
        result = await session.execute(select(Report).where(Report.status == "open").order_by(Report.id.desc()).limit(10))
        reports = result.scalars().all()
    lang = user.preferred_language
    if not reports:
        await message.answer(t("no_open_reports", lang), reply_markup=admin_panel_kb(lang))
    else:
        lines = [t("admin_reports_header", lang)]
        for r in reports:
            lines.append(f"#{r.id} reporter={r.reporter_user_id} reported={r.reported_user_id} reason={html.escape(r.reason)}")
        lines.append(t("admin_reports_footer", lang))
        await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))


@router.message(Command("report_view"))
@router.message(Command("admin_report"))
async def cmd_report_view(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        arg = (command.args or "").strip()
        if not arg.isdigit():
            await message.answer(t("admin_report_usage", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        report = (await session.execute(select(Report).where(Report.id == int(arg)))).scalar_one_or_none()
        if not report:
            await message.answer(t("admin_report_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        recent = report.recent_messages or "No recent messages saved."
        text = (
            f"⚠️ <b>Report #{report.id}</b>\n"
            f"Status: {html.escape(report.status)}\n"
            f"Reporter DB id: {report.reporter_user_id}\n"
            f"Reported DB id: {report.reported_user_id}\n"
            f"Match id: {report.match_id}\n"
            f"Reason: {html.escape(report.reason)}\n"
            f"Action: {html.escape(report.action_taken or '-')}\n\n"
            f"<b>Recent messages</b>\n<pre>{html.escape(recent)}</pre>\n"
            "Review: /review_report ID dismiss|warn|mute24|ban|block"
        )
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("review_report"))
@router.message(Command("admin_review_report"))
async def cmd_review_report(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        args = (command.args or "").split(maxsplit=1)
        if len(args) < 2 or not args[0].isdigit():
            await message.answer(t("admin_review_usage", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        report = (await session.execute(select(Report).where(Report.id == int(args[0])))).scalar_one_or_none()
        if not report:
            await message.answer(t("admin_report_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        report, status = await review_report(session, report, admin, args[1])
    await message.answer(f"Report #{report.id}: {status}. Action={report.action_taken or '-'}")


@router.message(Command("ban"))
@router.message(Command("admin_ban"))
async def cmd_ban(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        args = (command.args or "").split(maxsplit=1)
        if not args:
            await message.answer(t("admin_usage_ban", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        try:
            telegram_id = int(args[0])
        except ValueError:
            await message.answer(t("admin_invalid_id", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        reason = args[1] if len(args) > 1 else "Admin ban"
        user = await get_user_by_telegram(session, telegram_id)
        if not user:
            await message.answer(t("admin_user_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        await ban_user(session, user, reason, admin=admin)
    await message.answer(f"Banned {telegram_id}: {reason}")


@router.message(Command("unban"))
@router.message(Command("admin_unban"))
async def cmd_unban(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        arg = (command.args or "").strip()
        if not arg:
            await message.answer(t("admin_usage_unban", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        try:
            telegram_id = int(arg)
        except ValueError:
            await message.answer(t("admin_invalid_id", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        user = await get_user_by_telegram(session, telegram_id)
        if not user:
            await message.answer(t("admin_user_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        await unban_user(session, user, admin=admin)
    await message.answer(f"Unbanned {telegram_id}")


@router.message(Command("mute"))
@router.message(Command("admin_mute"))
async def cmd_mute(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        args = (command.args or "").split(maxsplit=2)
        if len(args) < 2:
            await message.answer(t("admin_usage_mute", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        try:
            telegram_id = int(args[0]); hours = int(args[1])
        except ValueError:
            await message.answer(t("admin_invalid_payment_args", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        target = await get_user_by_telegram(session, telegram_id)
        if not target:
            await message.answer(t("admin_user_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        reason = args[2] if len(args) > 2 else "Admin mute"
        await mute_user(session, target, hours, reason, admin=admin)
    await message.answer(f"Muted {telegram_id} for {hours}h: {reason}")


@router.message(Command("unmute"))
@router.message(Command("admin_unmute"))
async def cmd_unmute(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        arg = (command.args or "").strip()
        if not arg:
            await message.answer(t("admin_usage_unban", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        try:
            telegram_id = int(arg)
        except ValueError:
            await message.answer(t("admin_invalid_id", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        target = await get_user_by_telegram(session, telegram_id)
        if not target:
            await message.answer(t("admin_user_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        await unmute_user(session, target, admin=admin)
    await message.answer(f"Unmuted {telegram_id}")


@router.message(Command("trust"))
@router.message(Command("admin_trust"))
async def cmd_trust(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        arg = (command.args or "").strip()
        if not arg:
            await message.answer(t("admin_invalid_id", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        try:
            telegram_id = int(arg)
        except ValueError:
            await message.answer(t("admin_invalid_id", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        target = await get_user_by_telegram(session, telegram_id)
        if not target:
            await message.answer(t("admin_user_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        history = await get_ban_history(session, target.id, limit=5)
        hist = "\n".join(f"• {h.action}: {h.reason or '-'}" for h in history) or "No ban/mute history."
        muted = target.muted_until.isoformat(sep=' ', timespec='minutes') if target.muted_until else '-'
        text = (
            f"👤 User {target.telegram_id}\n"
            f"Trust: {target.trust_score}/100\nWarnings: {target.warning_count}\nBanned: {target.is_banned}\nMuted until: {muted}\n\nHistory:\n{hist}"
        )
    await message.answer(text)


@router.message(Command("ban_history"))
@router.message(Command("admin_ban_history"))
async def cmd_ban_history(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        arg = (command.args or "").strip()
        if not arg:
            await message.answer(t("admin_invalid_id", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        try:
            telegram_id = int(arg)
        except ValueError:
            await message.answer(t("admin_invalid_id", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        target = await get_user_by_telegram(session, telegram_id)
        if not target:
            await message.answer(t("admin_user_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        history = await get_ban_history(session, target.id, limit=15)
    if not history:
        await message.answer("No ban/mute history.")
    else:
        await message.answer("\n".join(f"#{h.id} {h.action} — {h.reason or '-'}" for h in history))


@router.message(Command("grant"))
@router.message(Command("admin_grant"))
async def cmd_grant(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, admin):
            return
        args = (command.args or "").split()
        if len(args) < 2:
            await message.answer(t("admin_usage_grant", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        try:
            telegram_id = int(args[0])
        except ValueError:
            await message.answer(t("admin_invalid_id", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        plan = args[1].lower()
        if plan not in {"free", "plus", "pro"}:
            await message.answer(t("admin_invalid_plan", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        days = None
        if len(args) >= 3:
            try:
                days = int(args[2])
            except ValueError:
                days = None
        target = await grant_plan(session, telegram_id, plan, days=days)
        if not target:
            await message.answer(t("admin_user_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        lang = admin.preferred_language
    await message.answer(t("grant_ok", lang).format(plan=plan))


@router.message(Command("mock_pay"))
async def cmd_mock_pay(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            return
        if not mock_payments_enabled():
            await message.answer(t("mock_disabled", lang))
            return
        args = (command.args or "").split()
        if len(args) < 3:
            await message.answer(t("admin_usage_mock_pay", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        try:
            telegram_id = int(args[0])
            months = int(args[2])
        except ValueError:
            await message.answer(t("admin_invalid_payment_args", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        plan = args[1].lower()
        target = await get_user_by_telegram(session, telegram_id)
        if not target:
            await message.answer(t("admin_user_not_found", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        if plan not in {"plus", "pro"} or months not in {1, 3, 6, 12}:
            await message.answer(t("admin_invalid_plan", admin.preferred_language), reply_markup=admin_panel_kb(admin.preferred_language))
            return
        target = await mock_activate_plan(session, target, plan, months)
    await message.answer(t("mock_payment_done", lang).format(plan=plan, months=months))




@router.message(Command("health"))
@router.message(Command("admin_health"))
async def cmd_health(message: Message) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        if not await require_admin(message, session, user):
            return
        db_ok = await db_health()
        redis_ok = await redis_health()
        settings_local = get_settings()
    await message.answer(
        "🩺 Health\n"
        f"DB: {'ok' if db_ok else 'down'}\n"
        f"Redis: {'ok' if redis_ok else 'not configured/down'}\n"
        f"Mode: {settings_local.bot_mode}\n"
        f"Env: {settings_local.app_env}"
    )


@router.message(ChatStates.changing_language)
async def change_language_state(message: Message, state: FSMContext) -> None:
    new_lang = choice_to_lang(message.text)
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        old_lang = user.preferred_language
        if not new_lang:
            await message.answer(t("invalid_language", old_lang), reply_markup=language_kb())
            return
        await update_language(session, user, new_lang)
        is_admin = admin_username_allowed(message.from_user) or user.is_admin
        if is_admin:
            user.is_admin = True
            user.onboarded = True
            await session.commit()
    await state.clear()
    if is_admin:
        await message.answer(t("admin_language_changed", new_lang), reply_markup=admin_panel_kb(new_lang))
    else:
        await message.answer(t("language_updated", new_lang), reply_markup=menu_kb(new_lang))


@router.message(ChatStates.changing_mood)
async def change_mood_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        action = action_from_text(message.text or "")
        if action == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=profile_kb(lang))
            return
        mood = mood_from_text(message.text)
        if not mood:
            await message.answer(t("invalid_mood", lang), reply_markup=mood_kb(lang))
            return
        await update_chat_mood(session, user, mood)
    await state.clear()
    await message.answer(t("mood_updated", lang), reply_markup=profile_kb(lang))


@router.message(ChatStates.editing_name)
async def edit_name_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        action = action_from_text(message.text or "")
        if action == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=profile_kb(lang))
            return
        name = (message.text or "").strip()
        if not valid_anon_name(name):
            await message.answer(t("bad_name", lang), reply_markup=cancel_kb(lang))
            return
        await update_anon_name(session, user, name)
        user.onboarded = True
        await session.commit()
    await state.clear()
    await message.answer(t("name_updated", lang), reply_markup=profile_kb(lang))


@router.message(ChatStates.offering_movie)
async def movie_code_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        action = action_from_text(message.text or "")
        if action == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=chat_kb(lang))
            return
        match = await get_active_match(session, user.id)
        if not match:
            await state.clear()
            await message.answer(t("not_in_chat", lang), reply_markup=menu_kb(lang))
            return
        movie = await get_movie(session, (message.text or "").strip())
        if not movie:
            await state.clear()
            await message.answer(t("movie_not_found", lang), reply_markup=chat_kb(lang))
            return
        other = await get_other_user(session, match, user.id)
        if not other:
            await state.clear()
            return
        offer = await create_movie_offer(session, match, user.id, movie)
        other_lang = other.preferred_language
    await state.clear()
    await message.answer(t("offer_sent", lang), reply_markup=chat_kb(lang))
    await message.bot.send_message(
        other.telegram_id,
        f"{t('offer_received', other_lang)}\n\n{movie_card(movie, other_lang)}",
        reply_markup=movie_offer_kb(offer.id, other_lang),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("offer:"))
async def offer_callback(call: CallbackQuery) -> None:
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer("Invalid", show_alert=True)
        return
    action, offer_id = parts[1], int(parts[2])
    async with SessionLocal() as session:
        user = await get_or_create_user(session, call.from_user)
        lang = user.preferred_language
        offer = await get_offer(session, offer_id)
        if not offer or offer.status != "pending":
            await call.answer(t("already_handled", lang), show_alert=True)
            return
        match = await get_active_match(session, user.id)
        if not match or match.id != offer.match_id:
            await call.answer(t("not_your_offer", lang), show_alert=True)
            return
        offerer = await get_user_by_id(session, offer.offered_by_user_id)
        movie = await get_movie_by_id(session, offer.movie_id)
        if not offerer or not movie:
            await call.answer(t("missing_data", lang), show_alert=True)
            return
        if action == "accept":
            ok_me, used_me, limit_me, period_me = await consume_movie_unlock(session, user)
            if not ok_me:
                await call.message.answer(t("movie_limit", lang).format(used=used_me, limit=limit_me, period=period_me), reply_markup=chat_kb(lang))
                await send_upgrade_prompt(call.message, user, "upgrade_movie_limit")
                return
            ok_other, used_other, limit_other, period_other = await consume_movie_unlock(session, offerer)
            if not ok_other:
                await refund_movie_unlock(session, user)
                await call.message.answer(t("movie_partner_limit", lang), reply_markup=chat_kb(lang))
                await call.bot.send_message(offerer.telegram_id, t("movie_limit", offerer.preferred_language).format(used=used_other, limit=limit_other, period=period_other), reply_markup=chat_kb(offerer.preferred_language))
                if not offerer.is_admin and offerer.plan != "pro":
                    await call.bot.send_message(offerer.telegram_id, t("upgrade_movie_limit", offerer.preferred_language), parse_mode=ParseMode.HTML, reply_markup=premium_upgrade_kb(offerer.preferred_language))
                return
            offer.status = "accepted"
            await session.commit()
            await call.message.answer(t("offer_accepted", lang), reply_markup=chat_kb(lang))
            delivered_me = await safe_deliver_movie(call.bot, call.message.chat.id, movie, lang, reply_markup=chat_kb(lang), user_id=user.id)
            await call.bot.send_message(offerer.telegram_id, t("offer_accepted", offerer.preferred_language), reply_markup=chat_kb(offerer.preferred_language))
            delivered_other = await safe_deliver_movie(call.bot, offerer.telegram_id, movie, offerer.preferred_language, reply_markup=chat_kb(offerer.preferred_language), user_id=offerer.id)
            if not delivered_me:
                await refund_movie_unlock(session, user)
            if not delivered_other:
                await refund_movie_unlock(session, offerer)
        elif action == "reject":
            offer.status = "rejected"
            await session.commit()
            await call.message.answer(t("offer_rejected", lang), reply_markup=chat_kb(lang))
            await call.bot.send_message(offerer.telegram_id, t("offer_rejected", offerer.preferred_language), reply_markup=chat_kb(offerer.preferred_language))
        else:
            offer.status = "suggested_other"
            await session.commit()
            await call.message.answer(t("suggest_another", lang), reply_markup=chat_kb(lang))
            await call.bot.send_message(offerer.telegram_id, t("suggest_another", offerer.preferred_language), reply_markup=chat_kb(offerer.preferred_language))
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception as exc:
        logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
    await call.answer()


@router.callback_query(F.data.startswith("buy:"))
async def buy_callback(call: CallbackQuery) -> None:
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer("Invalid", show_alert=True)
        return
    plan = parts[1]
    try:
        months = int(parts[2])
    except ValueError:
        await call.answer("Invalid", show_alert=True)
        return
    async with SessionLocal() as session:
        user = await get_or_create_user(session, call.from_user)
        lang = user.preferred_language
        if plan not in {"plus", "pro"} or months not in {1, 3, 6, 12}:
            await call.answer(t("missing_data", lang), show_alert=True)
            return
        payment = await create_payment_invoice(session, user, plan, months)
        stars = payment.stars_amount
        title = t("payment_invoice_title", lang).format(plan=plan.capitalize(), months=months)
        description = t("payment_invoice_description", lang).format(plan=plan.capitalize())
    await call.message.answer_invoice(
        title=title,
        description=description,
        payload=payment.invoice_payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=stars)],
    )
    await call.answer(t("payment_created", lang))


@router.callback_query(F.data.startswith("mockpay:"))
async def mockpay_callback(call: CallbackQuery) -> None:
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer("Invalid", show_alert=True)
        return
    plan = parts[1]
    try:
        months = int(parts[2])
    except ValueError:
        await call.answer("Invalid", show_alert=True)
        return
    async with SessionLocal() as session:
        user = await get_or_create_user(session, call.from_user)
        lang = user.preferred_language
        if not mock_payments_enabled():
            await call.answer(t("mock_disabled", lang), show_alert=True)
            return
        if plan not in {"plus", "pro"} or months not in {1, 3, 6, 12}:
            await call.answer(t("missing_data", lang), show_alert=True)
            return
        user = await mock_activate_plan(session, user, plan, months)
    await call.message.answer(t("mock_payment_done", lang).format(plan=plan, months=months), reply_markup=menu_kb(lang))
    await call.answer()


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery) -> None:
    async with SessionLocal() as session:
        payment = await get_payment_by_payload(session, query.invoice_payload)
        if not payment or payment.status != "pending":
            await query.answer(ok=False, error_message="Payment not found or already handled.")
            return
        user = await get_user_by_id(session, payment.user_id)
        if not user or user.telegram_id != query.from_user.id:
            await query.answer(ok=False, error_message="Payment user mismatch.")
            return
        if query.currency != "XTR" or query.total_amount != payment.stars_amount:
            await query.answer(ok=False, error_message="Payment amount mismatch.")
            return
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message) -> None:
    successful = message.successful_payment
    if not successful:
        return
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        payment = await get_payment_by_payload(session, successful.invoice_payload)
        if (
            not payment
            or payment.user_id != user.id
            or payment.status not in {"pending", "succeeded", "mock"}
            or successful.currency != "XTR"
            or successful.total_amount != payment.stars_amount
        ):
            await message.answer(t("payment_failed", lang), reply_markup=menu_kb(lang))
            return
        if payment.status == "succeeded" and payment.telegram_payment_charge_id and payment.telegram_payment_charge_id != successful.telegram_payment_charge_id:
            await message.answer(t("payment_failed", lang), reply_markup=menu_kb(lang))
            return
        user = await complete_payment(
            session,
            payment,
            charge_id=successful.telegram_payment_charge_id,
            raw_payload=str(successful.model_dump()),
        )
        lang = user.preferred_language if user else lang
    await message.answer(t("payment_success", lang).format(plan=payment.plan, months=payment.duration_months), reply_markup=menu_kb(lang))


@router.callback_query(F.data.startswith("report:"))
async def report_callback(call: CallbackQuery) -> None:
    parts = call.data.split(":")
    reason = parts[1] if len(parts) > 1 else "other"
    block_user = bool(int(parts[2])) if len(parts) > 2 and parts[2].isdigit() else False
    other = None
    async with SessionLocal() as session:
        user = await get_or_create_user(session, call.from_user)
        lang = user.preferred_language
        match = await get_active_match(session, user.id)
        if match:
            other = await get_other_user(session, match, user.id)
        report = await create_report(session, user, reason, block_user=block_user)
        auto_banned_other = False
        if other:
            fresh_other = await get_user_by_id(session, other.id)
            if fresh_other and fresh_other.is_banned:
                other = fresh_other
                auto_banned_other = True
        if block_user and match:
            await end_match(session, match, remember_pair=False)
    await call.message.answer(t("reported_blocked" if block_user else "reported", lang), reply_markup=menu_kb(lang) if block_user else chat_kb(lang))
    if auto_banned_other and other:
        await safe_send_to_user(call.bot, other, t("report_auto_ban_notice", other.preferred_language), reply_markup=menu_kb(other.preferred_language))
    if block_user and other:
        await safe_send_to_user(call.bot, other, t("you_were_blocked", other.preferred_language), reply_markup=menu_kb(other.preferred_language))
    await send_admins(
        call.bot,
        f"⚠️ Report #{report.id}\nReporter DB id: {report.reporter_user_id}\nReported DB id: {report.reported_user_id}\nReason: {reason}\nBlocked: {block_user}\n\nUse /report_view {report.id} or /review_report {report.id} warn|mute24|ban|dismiss",
    )
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception as exc:
        logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
    await call.answer()




@router.message(RoomStates.choosing_type)
async def room_type_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        action = action_from_text(message.text or "")
        if action == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=rooms_kb(lang))
            return
        if action not in {"create_public_room", "create_private_room"}:
            await message.answer(t("room_choose_type", lang), reply_markup=room_type_kb(lang))
            return
        await state.update_data(is_private=(action == "create_private_room"))
    await state.set_state(RoomStates.entering_title)
    await message.answer(t("room_enter_title", lang), reply_markup=room_title_kb(lang))


@router.message(RoomStates.entering_title)
async def room_title_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        action = action_from_text(message.text or "")
        if action == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=rooms_kb(lang))
            return
        data = await state.get_data()
        is_private = bool(data.get("is_private"))
        title = None if action == "auto_title" else (message.text or "").strip()
        try:
            room = await create_room(session, user, title=title, is_private=is_private)
        except PermissionError:
            await state.clear()
            await message.answer(t("premium_required", lang), reply_markup=rooms_kb(lang))
            return
        count = await room_member_count_safe(session, room.id)
    await state.clear()
    await message.answer(room_info_text(room, count, lang), parse_mode=ParseMode.HTML, reply_markup=room_kb(lang))


@router.message(RoomStates.joining_by_code)
async def room_join_code_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        action = action_from_text(message.text or "")
        if action == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=rooms_kb(lang))
            return
        room = await get_room_by_invite(session, message.text or "")
        if not room:
            await message.answer(t("room_invite_not_found", lang), reply_markup=cancel_kb(lang))
            return
        if room.is_private and not can_join_private_rooms(user):
            await message.answer(t("room_join_premium_required", lang), reply_markup=rooms_kb(lang))
            await send_upgrade_prompt(message, user, "upgrade_room_create")
            return
        try:
            await join_room(session, user, room)
        except PermissionError:
            await message.answer(t("room_join_premium_required", lang), reply_markup=rooms_kb(lang))
            return
        except ValueError:
            await message.answer(t("room_full", lang), reply_markup=rooms_kb(lang))
            return
        others = await get_room_users(session, room.id, exclude_user_id=user.id)
    await state.clear()
    await message.answer(t("room_joined", lang), reply_markup=room_kb(lang))
    for member in others:
        try:
            await message.bot.send_message(member.telegram_id, t("room_joined", member.preferred_language), reply_markup=room_kb(member.preferred_language))
        except Exception as exc:
            logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)


@router.message(RoomStates.offering_movie)
async def room_movie_code_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        action = action_from_text(message.text or "")
        if action == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=room_kb(lang))
            return
        room = await get_active_room(session, user.id)
        if not room:
            await state.clear()
            await message.answer(t("not_in_room", lang), reply_markup=rooms_kb(lang))
            return
        member = await get_room_member(session, room.id, user.id)
        if member and member.is_muted:
            await state.clear()
            await message.answer(t("you_are_muted", lang), reply_markup=room_kb(lang))
            return
        movie = await get_movie(session, (message.text or "").strip())
        if not movie:
            await state.clear()
            await message.answer(t("movie_not_found", lang), reply_markup=room_kb(lang))
            return
        offer = await create_room_movie_offer(session, room, user, movie)
        users = await get_room_users(session, room.id)
    await state.clear()
    for member_user in users:
        try:
            ml = member_user.preferred_language
            await message.bot.send_message(
                member_user.telegram_id,
                f"{t('room_offer_started', ml)}\n\n{movie_card(movie, ml)}\n\n{t('room_vote_result', ml).format(yes=offer.yes_votes_count, no=offer.no_votes_count, total=len(users))}",
                parse_mode=ParseMode.HTML,
                reply_markup=room_movie_vote_kb(offer.id, ml),
            )
        except Exception as exc:
            logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)


@router.callback_query(F.data.startswith("roomjoin:"))
async def public_room_join_callback(call: CallbackQuery, state: FSMContext) -> None:
    action = (call.data or "").split(":", 1)[1]
    async with SessionLocal() as session:
        user = await get_or_create_user(session, call.from_user)
        lang = user.preferred_language
        if action == "back":
            await call.answer()
            if call.message:
                try:
                    await call.message.edit_text(t("rooms_menu", lang), parse_mode=ParseMode.HTML, reply_markup=None)
                except Exception as exc:
                    logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
                await call.message.answer(t("rooms_menu", lang), reply_markup=rooms_kb(lang), parse_mode=ParseMode.HTML)
            return
        if not can_join_rooms(user):
            await call.answer(t("room_join_premium_required", lang), show_alert=True)
            return
        if await get_active_match(session, user.id):
            await call.answer(t("finish_chat_first", lang), show_alert=True)
            return
        if await get_active_room(session, user.id):
            await call.answer(t("already_in_room", lang), show_alert=True)
            return
        room = None
        if action == "random":
            room = await find_public_room(session, user)
        else:
            try:
                room_id = int(action)
            except ValueError:
                room_id = 0
            room = (await session.execute(select(Room).where(Room.id == room_id))).scalar_one_or_none()
        if not room:
            await call.answer(t("room_selected_unavailable", lang), show_alert=True)
            if call.message:
                await show_public_room_list(call.message, session, user)
            return
        if call.message:
            await join_selected_public_room(call.message, state, session, user, room)
        await call.answer()


@router.callback_query(F.data.startswith("roomoffer:"))
async def room_offer_callback(call: CallbackQuery) -> None:
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer("Invalid", show_alert=True)
        return
    vote_value, offer_id = parts[1], int(parts[2])
    async with SessionLocal() as session:
        user = await get_or_create_user(session, call.from_user)
        lang = user.preferred_language
        offer = await get_room_offer(session, offer_id)
        if not offer:
            await call.answer(t("missing_data", lang), show_alert=True)
            return
        room = (await session.execute(select(Room).where(Room.id == offer.room_id))).scalar_one_or_none()
        if not room or not await get_room_member(session, room.id, user.id):
            await call.answer(t("not_in_room", lang), show_alert=True)
            return
        if offer.status != "voting":
            await call.answer(t("room_offer_closed", lang), show_alert=True)
            return
        offer, result = await vote_room_movie_offer(session, offer, user, vote_value)
        movie = await get_movie_by_id(session, offer.movie_id)
        users = await get_room_users(session, room.id)
        total = len(users)
    await call.answer(t("room_vote_registered", lang))
    if result == "accepted" and movie:
        async with SessionLocal() as session2:
            # Re-check limits in a fresh session after the vote is resolved.
            refreshed_users = []
            for u in users:
                dbu = await get_user_by_id(session2, u.id)
                if dbu:
                    refreshed_users.append(dbu)
            for u in refreshed_users:
                ok, used, limit, period = await consume_movie_unlock(session2, u)
                try:
                    if ok:
                        await call.bot.send_message(u.telegram_id, t("room_movie_accepted", u.preferred_language).format(url=movie.legal_watch_url or ""), reply_markup=room_kb(u.preferred_language))
                        delivered = await safe_deliver_movie(call.bot, u.telegram_id, movie, u.preferred_language, reply_markup=room_kb(u.preferred_language), user_id=u.id)
                        if not delivered:
                            await refund_movie_unlock(session2, u)
                    else:
                        await call.bot.send_message(u.telegram_id, t("movie_limit", u.preferred_language).format(used=used, limit=limit, period=period), reply_markup=room_kb(u.preferred_language))
                        if not u.is_admin and u.plan != "pro":
                            await call.bot.send_message(u.telegram_id, t("upgrade_movie_limit", u.preferred_language), parse_mode=ParseMode.HTML, reply_markup=premium_upgrade_kb(u.preferred_language))
                except Exception as exc:
                    logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
                    if ok:
                        await refund_movie_unlock(session2, u)
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception as exc:
            logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
    elif result == "rejected":
        for u in users:
            try:
                await call.bot.send_message(u.telegram_id, t("room_movie_rejected", u.preferred_language), reply_markup=room_kb(u.preferred_language))
            except Exception as exc:
                logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception as exc:
            logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
    else:
        try:
            await call.message.edit_text(
                f"{call.message.html_text}\n\n{t('room_vote_result', lang).format(yes=offer.yes_votes_count, no=offer.no_votes_count, total=total)}",
                reply_markup=room_movie_vote_kb(offer.id, lang),
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)


@router.callback_query(F.data.startswith("roomreport:"))
async def room_report_callback(call: CallbackQuery) -> None:
    target_id = int(call.data.split(":", 1)[1]) if call.data and call.data.split(":", 1)[1].isdigit() else 0
    async with SessionLocal() as session:
        user = await get_or_create_user(session, call.from_user)
        lang = user.preferred_language
        room = await get_active_room(session, user.id)
        if not room:
            await call.answer(t("not_in_room", lang), show_alert=True)
            return
        if target_id <= 0 or target_id == user.id:
            await call.answer(t("missing_data", lang), show_alert=True)
            return
        member = await get_room_member(session, room.id, target_id)
        target = await get_user_by_id(session, target_id)
        if not member or member.left_at or not target:
            await call.answer(t("missing_data", lang), show_alert=True)
            return
        report = await create_room_report(session, user, target, room, reason="room_report")
    await call.answer(t("room_reported", lang), show_alert=True)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception as exc:
        logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
    await send_admins(call.bot, f"⚠️ Room report #{report.id}: reporter={user.telegram_id}, reported={target.telegram_id}, room={room.id}")


@router.callback_query(F.data.startswith("roomctl:"))
async def room_control_callback(call: CallbackQuery) -> None:
    parts = call.data.split(":")
    action = parts[1] if len(parts) > 1 else "none"
    target_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    if action == "none":
        await call.answer()
        return
    async with SessionLocal() as session:
        user = await get_or_create_user(session, call.from_user)
        lang = user.preferred_language
        room = await get_active_room(session, user.id)
        if not room:
            await call.answer(t("not_in_room", lang), show_alert=True)
            return
        if not await is_room_host(session, room, user.id):
            await call.answer(t("host_only", lang), show_alert=True)
            return
        target = await get_user_by_id(session, target_id)
        if not target:
            await call.answer(t("missing_data", lang), show_alert=True)
            return
        if action == "mute":
            member = await get_room_member(session, room.id, target_id)
            if not member:
                await call.answer(t("missing_data", lang), show_alert=True)
                return
            new_muted = not member.is_muted
            await set_room_member_mute(session, room, user, target_id, new_muted)
            await call.answer(t("room_member_muted" if new_muted else "room_member_unmuted", lang))
            try:
                await call.bot.send_message(target.telegram_id, t("you_are_muted", target.preferred_language) if new_muted else t("room_member_unmuted", target.preferred_language), reply_markup=room_kb(target.preferred_language))
            except Exception as exc:
                logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
        elif action == "kick":
            await kick_room_member(session, room, user, target_id)
            await call.answer(t("room_member_kicked", lang))
            try:
                await call.bot.send_message(target.telegram_id, t("you_were_kicked", target.preferred_language), reply_markup=menu_kb(target.preferred_language))
            except Exception as exc:
                logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)
        members = await get_room_members(session, room.id)
    try:
        await call.message.edit_reply_markup(reply_markup=host_controls_kb(members, lang))
    except Exception as exc:
        logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)



async def premium_flow(message: Message, session, user: User) -> None:
    lang = user.preferred_language
    expires = ""
    if user.plan_expires_at:
        expires = t("premium_expires", lang).format(date=user.plan_expires_at.strftime("%Y-%m-%d"))
    await message.answer(
        t("premium_page", lang).format(
            plan=html.escape(user.plan or "free"),
            expires=expires,
            free_skips=settings.free_daily_skips,
            plus_skips=settings.plus_daily_skips,
            pro_skips=settings.pro_daily_skips,
            free_movies=settings.free_daily_movie_unlocks,
            plus_movies=settings.plus_monthly_movie_unlocks,
        ) + "\n\n" + t("premium_payment_note", lang) + "\n\n" + t("premium_choose_plan", lang),
        parse_mode=ParseMode.HTML,
        reply_markup=premium_buy_kb(lang),
    )

def room_info_text(room: Room, count: int, lang: str) -> str:
    return t("room_info", lang).format(
        title=html.escape(room.title),
        privacy=t("privacy_private" if room.is_private else "privacy_public", lang),
        code=html.escape(room.invite_code),
        count=count,
        limit=room.max_members,
        mood=mood_label(room.mood, lang),
    )


async def room_member_count_safe(session, room_id: int) -> int:
    result = await session.execute(
        select(func.count(RoomMember.id)).where(RoomMember.room_id == room_id, RoomMember.left_at.is_(None))
    )
    return int(result.scalar_one())

@router.message(ChatStates.clean_confirm)
async def clean_confirm_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        action = action_from_text(message.text or "")
        if action == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=menu_kb(lang))
            return
        if action != "confirm_clean":
            await message.answer(t("clean_confirm", lang), reply_markup=clean_confirm_kb(lang))
            return
    await perform_clean_reset(message, state)


@router.message(ChatStates.watch_alone_code)
async def watch_alone_code_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        if action_from_text(message.text or "") == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=menu_kb(lang))
            return
        ok = await send_movie_to_user(message, session, user, (message.text or "").strip())
    if ok:
        await state.clear()


async def send_upgrade_prompt(message: Message, user: User, key: str, *, reply_markup=None) -> None:
    if user.is_admin or user.plan == "pro":
        return
    lang = user.preferred_language
    await message.answer(t(key, lang), parse_mode=ParseMode.HTML, reply_markup=reply_markup or premium_upgrade_kb(lang))


async def maybe_send_scheduled_ad(message: Message, session, user: User) -> None:
    show, ad = await should_show_ad_now(session, user)
    if not show or not ad:
        return
    try:
        await message.bot.copy_message(message.chat.id, ad.source_chat_id, ad.source_message_id)
        await send_upgrade_prompt(message, user, "upgrade_after_ad")
    except Exception as exc:
        # Ads must never break the core chat-search flow.
        logger.debug("Scheduled ad copy failed ad_id=%s user=%s: %s", ad.id, user.id, exc, exc_info=True)


@router.message(AdminAdStates.waiting_post)
async def admin_ad_post_state(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        admin = await get_or_create_user(session, message.from_user)
        lang = admin.preferred_language
        if not await require_admin(message, session, admin):
            await state.clear()
            return
        if message.text and action_from_text(message.text or "") == "cancel":
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=admin_panel_kb(lang))
            return
        try:
            await create_ad_campaign(session, admin, message.chat.id, message.message_id)
        except Exception as exc:
            logger.warning("Admin ad creation failed admin_id=%s: %s", admin.id, exc, exc_info=True)
            await message.answer(t("admin_ad_failed", lang), reply_markup=cancel_kb(lang))
            return
    await state.clear()
    await message.answer(
        t("admin_ad_saved", lang).format(free=settings.free_ad_interval, plus=settings.plus_ad_interval),
        reply_markup=admin_panel_kb(lang),
    )


@router.message(F.text)
async def text_handler(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        active, restriction = await is_telegram_restricted(session, user.telegram_id)
        if active and not user.is_admin:
            await message.answer(t("banned_until", lang).format(time=restriction_remaining_text(restriction)))
            return
        if user.is_banned and not user.is_admin:
            await message.answer(t("banned", lang))
            return
        action = action_from_text(message.text or "")

        if action and action.startswith("admin_"):
            if not await require_admin(message, session, user):
                return
            if action == "admin_stats":
                await message.answer(await admin_stats_text(session, lang), reply_markup=admin_panel_kb(lang))
                return
            if action == "admin_language":
                await state.clear()
                await state.set_state(ChatStates.changing_language)
                await message.answer(t("admin_choose_language", lang), reply_markup=language_kb())
                return
            if action == "admin_create_movie":
                await state.clear()
                await state.set_state(AdminMovieStates.code)
                await message.answer(t("admin_add_movie_start", lang), reply_markup=admin_movie_code_kb(lang), parse_mode=ParseMode.HTML)
                return
            if action == "admin_movies":
                movies = await list_movies(session, status=None, limit=500)
                if not movies:
                    await message.answer(t("admin_movie_list_empty", lang), reply_markup=admin_panel_kb(lang))
                    return
                lines = [t("admin_movie_list_header", lang), ""]
                for i, m in enumerate(movies, 1):
                    lines.append(f"{i}. <code>{html.escape(m.code)}</code> — {html.escape(m.title)} [{html.escape(m.status)}]")
                lines.append(t("admin_movie_list_footer", lang))
                await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))
                return
            if action == "admin_delete_movie":
                movies = await list_movies(session, status=None, limit=500)
                if not movies:
                    await message.answer(t("admin_movie_list_empty", lang), reply_markup=admin_panel_kb(lang))
                    return
                await state.set_state(AdminMovieStates.delete_number)
                await message.answer(t("admin_delete_choose_number", lang).format(movies=html.escape(format_numbered_movies(movies))), reply_markup=cancel_kb(lang), parse_mode=ParseMode.HTML)
                return
            if action == "admin_post_template":
                movies = await list_movies(session, status=None, limit=500)
                if not movies:
                    await message.answer(t("admin_movie_list_empty", lang), reply_markup=admin_panel_kb(lang))
                    return
                await state.set_state(AdminMovieStates.post_number)
                await message.answer(t("admin_post_choose_number", lang).format(movies=html.escape(format_numbered_movies(movies))), reply_markup=cancel_kb(lang), parse_mode=ParseMode.HTML)
                return
            if action == "admin_ads":
                await state.clear()
                await state.set_state(AdminAdStates.waiting_post)
                await message.answer(t("admin_ad_start", lang), reply_markup=cancel_kb(lang), parse_mode=ParseMode.HTML)
                return
            if action == "admin_reports":
                await cmd_admin_reports(message)
                return
        if action == "admin_panel":
            if await require_admin(message, session, user):
                await message.answer(t("admin_menu", lang), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))
            return
        if user.is_admin:
            # Admins never fall into normal user mode from old keyboards after Telegram refresh.
            await message.answer(t("admin_auto_only", lang), parse_mode=ParseMode.HTML, reply_markup=admin_panel_kb(lang))
            return
        if action == "watch_alone":
            await state.set_state(ChatStates.watch_alone_code)
            await message.answer(movie_code_prompt("watch_alone_intro", lang), reply_markup=cancel_kb(lang))
            return
        if action == "movies_list":
            url = movie_codes_channel_url()
            if not url:
                await message.answer(t("movies_channel_missing", lang), reply_markup=menu_kb(lang))
                return
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("open_movies_channel", lang), url=url)]])
            await message.answer(t("movies_channel_text", lang), reply_markup=kb)
            return
        if action == "clean":
            await perform_clean_reset(message, state)
            return

        if action == "find":
            await maybe_send_scheduled_ad(message, session, user)
            await find_chat(message, state, session, user)
            return
        if action == "cancel":
            await cancel_waiting_db(session, user.id)
            await state.clear()
            await message.answer(t("cancelled", lang), reply_markup=menu_kb(lang))
            return
        if action == "menu":
            await state.clear()
            active_match = await get_active_match(session, user.id)
            if active_match:
                await message.answer(t("chat_help", lang), reply_markup=chat_kb(lang))
            else:
                await message.answer(t("menu", lang), reply_markup=menu_kb(lang))
            return
        if action == "profile":
            await message.answer(
                t("profile_details", lang).format(
                    name=html.escape(user.anon_name),
                    language=lang_name(user.preferred_language, lang),
                    mood=mood_label(user.chat_mood, lang),
                ) + f"\n{ {'uz':'Reja', 'ru':'План', 'en':'Plan'}.get(lang, 'Plan') }: <b>{html.escape(user.plan or 'free')}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=profile_kb(lang),
            )
            return
        if action == "premium":
            await premium_flow(message, session, user)
            return
        if action == "usage":
            summary = await usage_summary(session, user)
            await message.answer(
                t("usage_page", lang).format(
                    plan=summary["plan"],
                    skips_used=summary["skips_used"],
                    skips_limit=summary["skips_limit"],
                    movie_used=summary["movie_used"],
                    movie_limit=summary["movie_limit"],
                    period=summary["movie_period"],
                ),
                reply_markup=menu_kb(lang),
            )
            return
        if action in {"language", "change_language"}:
            await state.set_state(ChatStates.changing_language)
            await message.answer(t("choose_lang", lang), reply_markup=language_kb())
            return
        if action == "change_mood":
            await state.set_state(ChatStates.changing_mood)
            await message.answer(t("choose_mood", lang), reply_markup=mood_kb(lang))
            return
        if action == "edit_name":
            if not can_edit_name_after_onboarding(user):
                await message.answer(t("name_edit_premium_required", lang), reply_markup=profile_kb(lang))
                return
            await state.set_state(ChatStates.editing_name)
            await message.answer(t("edit_name", lang), reply_markup=cancel_kb(lang))
            return
        if action == "rules":
            await message.answer(t("rules", lang), reply_markup=menu_kb(lang))
            return
        if action == "help":
            await message.answer(t("chat_help", lang), reply_markup=menu_kb(lang))
            return
        if action == "rooms":
            await close_inactive_rooms(session)
            await message.answer(t("rooms_menu", lang), reply_markup=rooms_kb(lang), parse_mode=ParseMode.HTML)
            return
        if action == "create_room":
            await create_room_flow(message, state, session, user)
            return
        if action == "join_public_room":
            await join_public_room_flow(message, state, session, user)
            return
        if action == "join_by_code":
            await join_by_code_flow(message, state, session, user)
            return
        if action == "my_room":
            await my_room_flow(message, session, user)
            return
        if action == "leave_room":
            await leave_room_flow(message, state, session, user)
            return
        if action == "members":
            await room_members_flow(message, session, user)
            return
        if action == "report_member":
            await room_report_member_flow(message, session, user)
            return
        if action == "room_info":
            await room_info_flow(message, session, user)
            return
        if action == "host_controls":
            await host_controls_flow(message, session, user)
            return
        if action == "offer_room_movie":
            await room_offer_movie_flow(message, state, session, user)
            return
        if action == "offer":
            match = await get_active_match(session, user.id)
            if not match:
                await message.answer(t("not_in_chat", lang), reply_markup=menu_kb(lang))
                return
            await state.set_state(ChatStates.offering_movie)
            await message.answer(movie_code_prompt("ask_movie_code", lang), reply_markup=cancel_kb(lang))
            return
        if action == "next":
            await next_person(message, state, session, user)
            return
        if action == "end":
            await end_chat(message, state, session, user)
            return
        if action == "report":
            await message.answer(t("report_reason", lang), reply_markup=report_kb(lang))
            return
        if action == "block":
            await block_current_user(message, state, session, user)
            return

        # Core rule: normal text is always anonymous chat text when a match exists.
        # Movie-looking text is NOT intercepted here. Movies only start after pressing Offer Movie.
        room = await get_active_room(session, user.id)
        if room:
            await relay_room_message(message, session, user, room)
            return

        match = await get_active_match(session, user.id)
        if match:
            await relay_message(message, session, user, match)
            return

        if await is_waiting(session, user.id):
            await message.answer(t("finding", lang).format(mood=mood_label(user.chat_mood, lang)), reply_markup=waiting_kb(lang))
            return

        # Idle users may type a movie code directly from the channel post.
        # Chat/room messages are already handled above, so this cannot steal
        # normal conversation text.
        candidate_code = normalize_watch_start_arg(message.text or "")
        if candidate_code and await get_movie(session, candidate_code):
            await send_movie_to_user(message, session, user, candidate_code)
            return

        await message.answer(t("menu", lang), reply_markup=menu_kb(lang))


@router.message()
async def media_handler(message: Message, state: FSMContext) -> None:
    """Handle photos/stickers/GIFs/audio/video with plan-based permissions."""
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user)
        lang = user.preferred_language
        active, restriction = await is_telegram_restricted(session, user.telegram_id)
        if active and not user.is_admin:
            await message.answer(t("banned_until", lang).format(time=restriction_remaining_text(restriction)))
            return
        if user.is_banned and not user.is_admin:
            await message.answer(t("banned", lang))
            return
        room = await get_active_room(session, user.id)
        if room:
            await relay_room_media_message(message, session, user, room)
            return
        match = await get_active_match(session, user.id)
        if match:
            await relay_media_message(message, session, user, match)
            return
        await message.answer(t("media_only_in_chat", lang), reply_markup=menu_kb(lang))


async def find_chat(message: Message, state: FSMContext, session, user: User) -> None:
    lang = user.preferred_language
    active_match = await get_active_match(session, user.id)
    if active_match:
        other_active = await get_other_user(session, active_match, user.id)
        other_restricted = False
        if other_active:
            other_restricted, _ = await is_telegram_restricted(session, other_active.telegram_id)
        stale_age = active_match.created_at and datetime.utcnow() - active_match.created_at > timedelta(hours=6)
        if not other_active or other_restricted or (other_active and other_active.is_banned) or stale_age:
            await end_match(session, active_match, remember_pair=False)
        else:
            await message.answer(t("chat_help", lang), reply_markup=chat_kb(lang))
            return
    expired_waiting = await prune_waiting(session)
    for expired in expired_waiting:
        await safe_delete(message.bot, expired.chat_id, expired.waiting_message_id)
        try:
            await message.bot.send_message(expired.chat_id, t("waiting_timeout", expired.lang), reply_markup=menu_kb(expired.lang))
        except TelegramForbiddenError:
            mark_bot_blocked(expired.telegram_id, expired.user_id)
        except TelegramBadRequest:
            pass
    if await is_waiting(session, user.id):
        await message.answer(t("already_waiting", lang), reply_markup=waiting_kb(lang))
        return
    waiting_msg = await message.answer(t("finding", lang).format(mood=mood_label(user.chat_mood, lang)), reply_markup=waiting_kb(lang))
    partner = await start_waiting(session, user, message.chat.id, waiting_msg.message_id)
    await state.set_state(ChatStates.waiting)
    if not partner:
        return
    await safe_delete(message.bot, message.chat.id, waiting_msg.message_id)
    await safe_delete(message.bot, partner.chat_id, partner.waiting_message_id)
    match = await create_match(session, user.id, partner.user_id)
    other = await get_user_by_id(session, partner.user_id)
    if not other:
        await end_match(session, match, remember_pair=False)
        await state.clear()
        await message.answer(t("partner_unavailable", lang), reply_markup=menu_kb(lang))
        return
    ok = await safe_send_to_user(
        message.bot,
        other,
        t("matched", other.preferred_language),
        reply_markup=chat_kb(other.preferred_language),
    )
    if not ok:
        await end_match(session, match, remember_pair=False)
        await state.clear()
        await message.answer(t("partner_unavailable", lang), reply_markup=menu_kb(lang))
        return
    await state.clear()
    await message.answer(t("matched", lang), reply_markup=chat_kb(lang))
    logger.info("Created match %s", match.id)


async def handle_filtered_text(message: Message, session, user: User, text: str, category: str, reply_markup) -> None:
    lang = user.preferred_language
    user, auto_banned = await add_warning(session, user, category, text)
    if auto_banned:
        active, restriction = await is_telegram_restricted(session, user.telegram_id)
        await message.answer(t("auto_banned_2h", lang).format(time=restriction_remaining_text(restriction)), reply_markup=menu_kb(lang))
        await send_admins(message.bot, f"⛔ Auto-banned user {user.telegram_id} for 2h after {user.warning_count} warnings. Reason: {category}")
        return
    await message.answer(t("message_blocked", lang).format(reason=t(f"filter_{category}", lang)), reply_markup=reply_markup)


async def relay_message(message: Message, session, user: User, match: Match) -> None:
    lang = user.preferred_language
    text = message.text or ""
    if is_user_muted(user) and not user.is_admin:
        await message.answer(t("muted", lang).format(time=muted_remaining_text(user)), reply_markup=chat_kb(lang))
        return
    mod = moderate_text_for_plan(user, text)
    if not mod.allowed:
        await save_chat(session, match.id, user.id, user.anon_name, text, msg_type="filtered", is_flagged=True, filter_reason=mod.category)
        await handle_filtered_text(message, session, user, text, mod.category or "other", chat_kb(lang))
        return
    other = await get_other_user(session, match, user.id)
    if not other:
        return
    try:
        await message.bot.send_chat_action(chat_id=other.telegram_id, action="typing")
        await asyncio.sleep(0.3)
    except TelegramForbiddenError:
        mark_bot_blocked(other.telegram_id, other.id)
    except TelegramBadRequest:
        pass
    await save_chat(session, match.id, user.id, user.anon_name, text)
    safe_text = html.escape(text)
    safe_name = html.escape(user.anon_name)
    ok = await safe_send_to_user(
        message.bot,
        other,
        f"<b>{safe_name}</b>:\n{safe_text}",
        parse_mode=ParseMode.HTML,
    )
    if not ok:
        await end_match(session, match, remember_pair=False)
        await message.answer(t("partner_unavailable", lang), reply_markup=menu_kb(lang))


async def relay_media_message(message: Message, session, user: User, match: Match) -> None:
    lang = user.preferred_language
    kind = message_kind(message)
    caption = message.caption or ""
    if is_user_muted(user) and not user.is_admin:
        await message.answer(t("muted", lang).format(time=muted_remaining_text(user)), reply_markup=chat_kb(lang))
        return
    if not media_allowed_for_user(user, kind):
        await message.answer(t("media_not_allowed", lang).format(plan=html.escape(user.plan or "free")), reply_markup=chat_kb(lang))
        return
    mod = moderate_text_for_plan(user, caption)
    if caption and not mod.allowed:
        await save_chat(session, match.id, user.id, user.anon_name, caption, msg_type="filtered", is_flagged=True, filter_reason=mod.category)
        await handle_filtered_text(message, session, user, caption, mod.category or "other", chat_kb(lang))
        return
    other = await get_other_user(session, match, user.id)
    if not other:
        return
    try:
        await message.bot.send_chat_action(chat_id=other.telegram_id, action="typing")
        await asyncio.sleep(0.3)
    except TelegramForbiddenError:
        mark_bot_blocked(other.telegram_id, other.id)
    except TelegramBadRequest:
        pass
    await save_chat(session, match.id, user.id, user.anon_name, f"[{kind}] {caption}".strip(), msg_type=kind)
    safe_name = html.escape(user.anon_name)
    target_lang = other.preferred_language
    label = media_kind_label(kind, target_lang)
    intro = f"<b>{safe_name}</b>: {html.escape(label)}"
    if caption:
        intro += f"\n{html.escape(caption)}"
    ok = await safe_send_to_user(message.bot, other, intro, parse_mode=ParseMode.HTML)
    if not ok:
        await end_match(session, match, remember_pair=False)
        await message.answer(t("partner_unavailable", lang), reply_markup=menu_kb(lang))
        return
    copied = await safe_copy_to_user(message.bot, other, message.chat.id, message.message_id)
    if not copied:
        await safe_send_to_user(message.bot, other, t("media_copy_failed", target_lang))


async def relay_room_media_message(message: Message, session, user: User, room: Room) -> None:
    lang = user.preferred_language
    kind = message_kind(message)
    caption = message.caption or ""
    if is_user_muted(user) and not user.is_admin:
        await message.answer(t("muted", lang).format(time=muted_remaining_text(user)), reply_markup=room_kb(lang))
        return
    member = await get_room_member(session, room.id, user.id)
    if member and member.is_muted:
        await message.answer(t("you_are_muted", lang), reply_markup=room_kb(lang))
        return
    if not media_allowed_for_user(user, kind):
        await message.answer(t("media_not_allowed", lang).format(plan=html.escape(user.plan or "free")), reply_markup=room_kb(lang))
        return
    mod = moderate_text_for_plan(user, caption)
    if caption and not mod.allowed:
        await handle_filtered_text(message, session, user, caption, mod.category or "other", room_kb(lang))
        return
    others = await get_room_users(session, room.id, exclude_user_id=user.id)
    if not others:
        await message.answer(t("room_help", lang), reply_markup=room_kb(lang))
        return
    await save_room_chat(session, room.id, user.id, user.anon_name, f"[{kind}] {caption}".strip())
    safe_name = html.escape(user.anon_name)
    for member_user in others:
        try:
            ml = member_user.preferred_language
            label = media_kind_label(kind, ml)
            intro = f"<b>{safe_name}</b>: {html.escape(label)}"
            if caption:
                intro += f"\n{html.escape(caption)}"
            await message.bot.send_message(member_user.telegram_id, intro, parse_mode=ParseMode.HTML)
            await message.bot.copy_message(member_user.telegram_id, message.chat.id, message.message_id)
        except Exception as exc:
            logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)


async def end_chat(message: Message, state: FSMContext, session, user: User) -> None:
    lang = user.preferred_language
    match = await get_active_match(session, user.id)
    if not match:
        await cancel_waiting_db(session, user.id)
        await state.clear()
        await message.answer(t("not_in_chat", lang), reply_markup=menu_kb(lang))
        return
    other = await get_other_user(session, match, user.id)
    await end_match(session, match)
    await state.clear()
    await message.answer(t("chat_ended", lang), reply_markup=menu_kb(lang))
    if other:
        await safe_send_to_user(message.bot, other, t("partner_left", other.preferred_language), reply_markup=menu_kb(other.preferred_language))


async def next_person(message: Message, state: FSMContext, session, user: User) -> None:
    lang = user.preferred_language
    ok, used, limit = await can_skip_today(session, user)
    if not ok:
        await message.answer(t("skip_limit", lang).format(used=used, limit=limit), reply_markup=chat_kb(lang))
        await send_upgrade_prompt(message, user, "upgrade_skip_limit")
        return
    match = await get_active_match(session, user.id)
    if not match:
        await message.answer(t("not_in_chat", lang), reply_markup=menu_kb(lang))
        return
    other = await get_other_user(session, match, user.id)
    await end_match(session, match)
    await record_skip(session, user)
    if other:
        await safe_send_to_user(message.bot, other, t("partner_left", other.preferred_language), reply_markup=menu_kb(other.preferred_language))
    await find_chat(message, state, session, user)


async def block_current_user(message: Message, state: FSMContext, session, user: User) -> None:
    lang = user.preferred_language
    match = await get_active_match(session, user.id)
    if not match:
        await message.answer(t("not_in_chat", lang), reply_markup=menu_kb(lang))
        return
    other = await get_other_user(session, match, user.id)
    if other:
        await create_block(session, user.id, other.id, reason="manual_block")
    await end_match(session, match, remember_pair=False)
    await state.clear()
    await message.answer(t("blocked", lang), reply_markup=menu_kb(lang))
    if other:
        await safe_send_to_user(message.bot, other, t("you_were_blocked", other.preferred_language), reply_markup=menu_kb(other.preferred_language))


def public_room_list_text(room_rows, lang: str) -> str:
    lines = []
    for n, (room, count) in enumerate(room_rows, start=1):
        lines.append(t("room_public_line", lang).format(
            n=n,
            title=html.escape(room.title),
            count=count,
            limit=room.max_members,
            mood=mood_label(room.mood, lang),
        ))
    body = "\n".join(lines) if lines else "—"
    return t("room_public_list", lang).format(rooms=body) + "\n\n" + t("room_public_hint", lang)


async def show_public_room_list(message: Message, session, user: User) -> None:
    lang = user.preferred_language
    rooms = await list_public_rooms(session, user, limit=8)
    if not rooms:
        await message.answer(t("room_no_public", lang), reply_markup=rooms_kb(lang))
        return
    await message.answer(
        public_room_list_text(rooms, lang),
        parse_mode=ParseMode.HTML,
        reply_markup=public_room_list_kb(rooms, lang),
    )


async def join_public_room_flow(message: Message, state: FSMContext, session, user: User) -> None:
    lang = user.preferred_language
    if not can_join_rooms(user):
        await message.answer(t("room_join_premium_required", lang), reply_markup=rooms_kb(lang))
        await send_upgrade_prompt(message, user, "upgrade_room_create")
        return
    if await get_active_match(session, user.id):
        await message.answer(t("finish_chat_first", lang), reply_markup=menu_kb(lang))
        return
    if await get_active_room(session, user.id):
        await message.answer(t("already_in_room", lang), reply_markup=room_kb(lang))
        return
    await show_public_room_list(message, session, user)


async def join_selected_public_room(message: Message, state: FSMContext, session, user: User, room: Room) -> None:
    lang = user.preferred_language
    if not room or room.status != "open" or room.is_private:
        await message.answer(t("room_selected_unavailable", lang), reply_markup=rooms_kb(lang))
        return
    try:
        await join_room(session, user, room)
    except PermissionError:
        await message.answer(t("room_join_premium_required", lang), reply_markup=rooms_kb(lang))
        return
    except ValueError:
        await message.answer(t("room_selected_unavailable", lang), reply_markup=rooms_kb(lang))
        return
    others = await get_room_users(session, room.id, exclude_user_id=user.id)
    count = await room_member_count_safe(session, room.id)
    await state.clear()
    await message.answer(
        t("room_joined_named", lang).format(title=html.escape(room.title)),
        reply_markup=room_kb(lang),
        parse_mode=ParseMode.HTML,
    )
    await message.answer(room_info_text(room, count, lang), parse_mode=ParseMode.HTML, reply_markup=room_kb(lang))
    for member in others:
        try:
            await message.bot.send_message(member.telegram_id, t("room_joined", member.preferred_language), reply_markup=room_kb(member.preferred_language))
        except Exception as exc:
            logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)


async def my_room_flow(message: Message, session, user: User) -> None:
    lang = user.preferred_language
    room = await get_active_room(session, user.id)
    if not room:
        await message.answer(t("not_in_room", lang), reply_markup=rooms_kb(lang))
        return
    members = await get_room_members(session, room.id)
    member_lines = "\n".join(f"• {html.escape(m.anon_name_snapshot)} ({m.role})" for m in members)
    await message.answer(t("room_members", lang).format(members=member_lines), reply_markup=room_kb(lang), parse_mode=ParseMode.HTML)


async def room_members_flow(message: Message, session, user: User) -> None:
    await my_room_flow(message, session, user)


async def room_report_member_flow(message: Message, session, user: User) -> None:
    lang = user.preferred_language
    room = await get_active_room(session, user.id)
    if not room:
        await message.answer(t("not_in_room", lang), reply_markup=rooms_kb(lang))
        return
    members = await get_room_members(session, room.id)
    members = [m for m in members if m.user_id != user.id and not m.left_at]
    await message.answer(t("room_report_choose", lang), reply_markup=room_report_members_kb(members, lang))


async def leave_room_flow(message: Message, state: FSMContext, session, user: User) -> None:
    lang = user.preferred_language
    room = await get_active_room(session, user.id)
    if not room:
        await message.answer(t("not_in_room", lang), reply_markup=menu_kb(lang))
        return
    others = await leave_room(session, user, room)
    await state.clear()
    await message.answer(t("room_left", lang), reply_markup=menu_kb(lang))
    for member in others:
        try:
            await message.bot.send_message(member.telegram_id, t("room_partner_left", member.preferred_language), reply_markup=room_kb(member.preferred_language))
        except Exception as exc:
            logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)


async def relay_room_message(message: Message, session, user: User, room: Room) -> None:
    lang = user.preferred_language
    text = message.text or ""
    if is_user_muted(user) and not user.is_admin:
        await message.answer(t("muted", lang).format(time=muted_remaining_text(user)), reply_markup=room_kb(lang))
        return
    member = await get_room_member(session, room.id, user.id)
    if member and member.is_muted:
        await message.answer(t("you_are_muted", lang), reply_markup=room_kb(lang))
        return
    mod = moderate_text_for_plan(user, text)
    if not mod.allowed:
        await handle_filtered_text(message, session, user, text, mod.category or "other", room_kb(lang))
        return
    others = await get_room_users(session, room.id, exclude_user_id=user.id)
    if not others:
        await message.answer(t("room_help", lang), reply_markup=room_kb(lang))
        return
    await save_room_chat(session, room.id, user.id, user.anon_name, text)
    safe_text = html.escape(text)
    safe_name = html.escape(user.anon_name)
    for member in others:
        try:
            await message.bot.send_message(
                member.telegram_id,
                f"<b>{safe_name}</b>:\n{safe_text}",
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            logger.debug("Suppressed Telegram/bot operation failure: %s", exc, exc_info=True)




# v10 overrides and new room flows.
async def create_room_flow(message: Message, state: FSMContext, session, user: User) -> None:
    lang = user.preferred_language
    if await get_active_match(session, user.id):
        await message.answer(t("finish_chat_first", lang), reply_markup=menu_kb(lang))
        return
    if await get_active_room(session, user.id):
        await message.answer(t("already_in_room", lang), reply_markup=room_kb(lang))
        return
    # Free users can join public rooms later if you choose, but creation stays premium.
    try:
        # quick permission check without actually creating a room
        from app.services import room_limit_for
        if room_limit_for(user) <= 0:
            raise PermissionError
    except PermissionError:
        await message.answer(t("premium_required", lang), reply_markup=rooms_kb(lang))
        await send_upgrade_prompt(message, user, "upgrade_room_create")
        return
    await state.set_state(RoomStates.choosing_type)
    await message.answer(t("room_choose_type", lang), reply_markup=room_type_kb(lang))


async def join_by_code_flow(message: Message, state: FSMContext, session, user: User) -> None:
    lang = user.preferred_language
    if not can_join_private_rooms(user):
        await message.answer(t("room_join_premium_required", lang), reply_markup=rooms_kb(lang))
        await send_upgrade_prompt(message, user, "upgrade_room_create")
        return
    if await get_active_match(session, user.id):
        await message.answer(t("finish_chat_first", lang), reply_markup=menu_kb(lang))
        return
    if await get_active_room(session, user.id):
        await message.answer(t("already_in_room", lang), reply_markup=room_kb(lang))
        return
    await state.set_state(RoomStates.joining_by_code)
    await message.answer(t("room_enter_invite", lang), reply_markup=cancel_kb(lang))


async def room_info_flow(message: Message, session, user: User) -> None:
    lang = user.preferred_language
    room = await get_active_room(session, user.id)
    if not room:
        await message.answer(t("not_in_room", lang), reply_markup=rooms_kb(lang))
        return
    count = await room_member_count_safe(session, room.id)
    await message.answer(room_info_text(room, count, lang), parse_mode=ParseMode.HTML, reply_markup=room_kb(lang))


async def host_controls_flow(message: Message, session, user: User) -> None:
    lang = user.preferred_language
    room = await get_active_room(session, user.id)
    if not room:
        await message.answer(t("not_in_room", lang), reply_markup=rooms_kb(lang))
        return
    if not await is_room_host(session, room, user.id):
        await message.answer(t("host_only", lang), reply_markup=room_kb(lang))
        return
    members = await get_room_members(session, room.id)
    await message.answer(t("room_members", lang).format(members="Host controls"), reply_markup=host_controls_kb(members, lang), parse_mode=ParseMode.HTML)


async def room_offer_movie_flow(message: Message, state: FSMContext, session, user: User) -> None:
    lang = user.preferred_language
    room = await get_active_room(session, user.id)
    if not room:
        await message.answer(t("not_in_room", lang), reply_markup=rooms_kb(lang))
        return
    member = await get_room_member(session, room.id, user.id)
    if member and member.is_muted:
        await message.answer(t("you_are_muted", lang), reply_markup=room_kb(lang))
        return
    await state.set_state(RoomStates.offering_movie)
    await message.answer(movie_code_prompt("room_ask_movie_code", lang), reply_markup=cancel_kb(lang))

def create_bot() -> Bot:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Add it to .env first.")
    return Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def create_dispatcher() -> Dispatcher:
    if not settings.redis_url:
        raise RuntimeError("REDIS_URL is required for durable FSM state. Start Redis and set REDIS_URL=redis://localhost:6379/0")
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)
    private_only = PrivateChatOnlyMiddleware()
    force_join = ForceJoinMiddleware()
    dp.message.outer_middleware(private_only)
    dp.callback_query.outer_middleware(private_only)
    dp.message.outer_middleware(force_join)
    dp.callback_query.outer_middleware(force_join)
    dp.include_router(router)
    return dp


async def run_polling() -> None:
    configure_logging()
    text_errors = validate_texts()
    if text_errors:
        for err in text_errors:
            logger.error("TEXT VALIDATION: %s", err)
        raise RuntimeError(f"texts.py has {len(text_errors)} missing translations. Fix before launch.")
    force_join_errors = validate_force_join_configuration()
    if force_join_errors:
        for err in force_join_errors:
            logger.error("FORCE_JOIN CONFIG: %s", err)
        raise RuntimeError("Invalid FORCE_JOIN configuration. Fix .env before launch.")
    await init_db()
    if not await redis_health():
        raise RuntimeError("Redis is required for durable FSM/rate state. Start Redis and set REDIS_URL correctly.")
    bot = create_bot()
    dp = create_dispatcher()
    await bot.delete_webhook(drop_pending_updates=settings.drop_pending_updates)
    logger.info("Starting polling mode")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_redis()
        await close_db()
        await bot.session.close()


async def run_bot() -> None:
    if settings.bot_mode == "webhook":
        logger.info("Webhook mode detected. Matching/FSM state is durable when DATABASE_URL and REDIS_URL are configured.")
        raise RuntimeError("BOT_MODE=webhook must be started with: uvicorn app.webhook_server:app --host 0.0.0.0 --port 8000")
    await run_polling()


def main() -> None:
    asyncio.run(run_bot())
