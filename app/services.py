from __future__ import annotations

from dataclasses import dataclass, field
import asyncio
import logging
import secrets
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, inspect as sa_inspect, or_, select, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import ActiveMatchParticipant, AdCampaign, BanHistory, Block, ChatMessage, Match, Movie, MovieOffer, PendingWatchIntent, Report, ReportStrike, ReservedAnonName, TelegramBlock, TelegramEntitlement, Room, RoomMember, RoomMessage, Payment, RoomMovieOffer, RoomMovieVote, TelegramRestriction, UsageDaily, UsageMonthly, User, UserWarning, WaitingQueue
from app.utils import FUNNY_ANON_NAMES, make_anon_name, make_invite_code

settings = get_settings()
logger = logging.getLogger(__name__)


def model_id(model: Any) -> int:
    state = sa_inspect(model)
    if state.identity:
        return int(state.identity[0])
    return int(model.id)


@dataclass
class WaitingUser:
    user_id: int
    telegram_id: int
    chat_id: int
    lang: str
    mood: str
    waiting_message_id: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


# Legacy in-process shims kept only for older tests and last-resort cleanup.
# Production matching/session state is recovered from the database below.
WAITING: dict[int, WaitingUser] = {}
ACTIVE: dict[int, int] = {}
ACTIVE_ROOM: dict[int, int] = {}
LAST_SEEN_TOUCH: dict[int, datetime] = {}
RECENT_PAIRS: dict[frozenset[int], datetime] = {}
RECENT_PAIR_TTL = timedelta(minutes=10)
WAITING_TTL = timedelta(minutes=3)
REPORT_MATCH_AVOID_TTL = timedelta(days=max(1, int(getattr(settings, "report_match_avoid_days", 14))))
BOT_BLOCKED_TELEGRAM_IDS: set[int] = set()
_MATCH_LOCK = asyncio.Lock()


def is_env_admin_id(telegram_id: int) -> bool:
    return int(telegram_id) in set(settings.admin_ids or [])


async def get_restriction(session: AsyncSession, telegram_id: int) -> TelegramRestriction | None:
    result = await session.execute(select(TelegramRestriction).where(TelegramRestriction.telegram_id == int(telegram_id)))
    return result.scalar_one_or_none()


async def is_telegram_restricted(session: AsyncSession, telegram_id: int) -> tuple[bool, TelegramRestriction | None]:
    restriction = await get_restriction(session, telegram_id)
    if not restriction or not restriction.banned_until:
        return False, restriction
    if restriction.banned_until <= datetime.utcnow():
        restriction.banned_until = None
        restriction.reason = None
        restriction.updated_at = datetime.utcnow()
        await session.commit()
        return False, restriction
    return True, restriction


def restriction_remaining_text(restriction: TelegramRestriction | None) -> str:
    if not restriction or not restriction.banned_until or restriction.banned_until <= datetime.utcnow():
        return ""
    delta = restriction.banned_until - datetime.utcnow()
    minutes = max(1, int(delta.total_seconds() // 60))
    if minutes >= 60:
        return f"{minutes // 60}h {minutes % 60}m"
    return f"{minutes}m"


async def restrict_telegram_id(session: AsyncSession, telegram_id: int, hours: int = 2, reason: str = "auto_restriction", *, user: User | None = None) -> TelegramRestriction:
    restriction = await get_restriction(session, telegram_id)
    if not restriction:
        restriction = TelegramRestriction(telegram_id=int(telegram_id))
        session.add(restriction)
    restriction.banned_until = datetime.utcnow() + timedelta(hours=max(1, int(hours)))
    restriction.reason = reason
    restriction.updated_at = datetime.utcnow()
    if user is not None:
        user.is_banned = True
        user.ban_reason = reason
    session.add(BanHistory(
        user_id=user.id if user else None,
        admin_user_id=None,
        action="auto_ban",
        reason=reason,
        starts_at=datetime.utcnow(),
        ends_at=restriction.banned_until,
    ))
    await session.commit()
    await session.refresh(restriction)
    return restriction


async def sync_user_admin_and_restriction(session: AsyncSession, user: User) -> User:
    changed = False
    if is_env_admin_id(user.telegram_id) and not user.is_admin:
        user.is_admin = True
        changed = True
    active, restriction = await is_telegram_restricted(session, user.telegram_id)
    if active and not user.is_admin:
        if not user.is_banned:
            user.is_banned = True
            changed = True
        if restriction and user.ban_reason != restriction.reason:
            user.ban_reason = restriction.reason
            changed = True
    elif not active and user.is_banned and not user.is_admin:
        user.is_banned = False
        user.ban_reason = None
        changed = True
    if changed:
        await session.commit()
        await session.refresh(user)
    return user


def _pair(a: int, b: int) -> frozenset[int]:
    return frozenset((a, b))


def remember_recent_pair(a: int, b: int) -> None:
    # Legacy compatibility only. Matching itself uses durable DB cooldown.
    RECENT_PAIRS[_pair(a, b)] = datetime.utcnow()


def is_recent_pair(a: int, b: int) -> bool:
    # Legacy compatibility only. Matching itself does not call this.
    now = datetime.utcnow()
    stale = [pair for pair, ts in RECENT_PAIRS.items() if now - ts > RECENT_PAIR_TTL]
    for pair in stale:
        RECENT_PAIRS.pop(pair, None)
    ts = RECENT_PAIRS.get(_pair(a, b))
    return bool(ts and now - ts <= RECENT_PAIR_TTL)


def mark_bot_blocked(telegram_id: int, user_id: int | None = None) -> None:
    """Mark a Telegram account that blocked the bot and remove it from volatile queues.

    This is intentionally in-memory: if the user later unblocks and sends /start,
    Telegram will deliver a new update and the account can be used again.
    """
    BOT_BLOCKED_TELEGRAM_IDS.add(int(telegram_id))
    if user_id is not None:
        WAITING.pop(int(user_id), None)
        ACTIVE.pop(int(user_id), None)
        ACTIVE_ROOM.pop(int(user_id), None)


def mark_bot_unblocked(telegram_id: int) -> None:
    BOT_BLOCKED_TELEGRAM_IDS.discard(int(telegram_id))


def is_bot_blocked(telegram_id: int) -> bool:
    return int(telegram_id) in BOT_BLOCKED_TELEGRAM_IDS


async def has_past_match_between(session: AsyncSession, a_id: int, b_id: int) -> bool:
    """True only when this exact pair has matched before.

    Kept for compatibility/tests. The matcher itself uses
    pair_in_rematch_cooldown(), because a small user base must allow natural
    accidental rematches after both people have talked to others.
    """
    result = await session.execute(
        select(Match.id)
        .where(
            or_(
                and_(Match.user_a_id == a_id, Match.user_b_id == b_id),
                and_(Match.user_a_id == b_id, Match.user_b_id == a_id),
            )
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def pair_in_rematch_cooldown(session: AsyncSession, a_id: int, b_id: int) -> bool:
    """Block only immediate same-pair rematches, not forever.

    Example with SAME_PAIR_REMATCH_AFTER_CHATS=1:
    A-B match and end -> A and B cannot meet immediately.
    A-C and B-D happen -> A-B may randomly meet again.

    Manual Block records still remain permanent and are checked separately.
    """
    required = max(0, int(getattr(settings, "same_pair_rematch_after_chats", 1)))
    if required <= 0:
        return False

    result = await session.execute(
        select(Match)
        .where(
            or_(
                and_(Match.user_a_id == a_id, Match.user_b_id == b_id),
                and_(Match.user_a_id == b_id, Match.user_b_id == a_id),
            )
        )
        .order_by(Match.id.desc())
        .limit(1)
    )
    last_pair_match = result.scalar_one_or_none()
    if not last_pair_match:
        return False

    async def other_chats_after(user_id: int) -> int:
        count_result = await session.execute(
            select(func.count(Match.id)).where(
                Match.id > last_pair_match.id,
                Match.status != "active",
                or_(Match.user_a_id == user_id, Match.user_b_id == user_id),
                ~or_(
                    and_(Match.user_a_id == a_id, Match.user_b_id == b_id),
                    and_(Match.user_a_id == b_id, Match.user_b_id == a_id),
                ),
            )
        )
        return int(count_result.scalar_one() or 0)

    return (await other_chats_after(a_id)) < required or (await other_chats_after(b_id)) < required


async def _waiting_from_row(row: WaitingQueue) -> WaitingUser:
    return WaitingUser(
        user_id=row.user_id,
        telegram_id=row.telegram_id,
        chat_id=row.chat_id,
        lang=row.lang,
        mood=row.mood,
        waiting_message_id=row.waiting_message_id,
        created_at=row.created_at,
    )


async def is_waiting(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(select(WaitingQueue.id).where(WaitingQueue.user_id == int(user_id)).limit(1))
    return result.scalar_one_or_none() is not None


async def waiting_count(session: AsyncSession) -> int:
    await prune_waiting(session, notify=False)
    result = await session.execute(select(func.count(WaitingQueue.id)))
    return int(result.scalar_one() or 0)


async def _delete_waiting_row(session: AsyncSession, user_id: int) -> None:
    WAITING.pop(int(user_id), None)
    await session.execute(delete(WaitingQueue).where(WaitingQueue.user_id == int(user_id)))


async def prune_waiting(session: AsyncSession, notify: bool = True) -> list[WaitingUser]:
    """Remove stale, banned, deleted, blocked-bot, or already-active waiting users.

    The durable queue lives in waiting_queue so restarts/webhook workers do not
    lose users who are searching. Legacy WAITING entries are still cleaned for
    backwards-compatible tests.
    """
    now = datetime.utcnow()
    expired: list[WaitingUser] = []

    result = await session.execute(select(WaitingQueue).order_by(WaitingQueue.created_at.asc()))
    db_rows = list(result.scalars().all()) if hasattr(result, "scalars") else []
    for row in db_rows:
        waiting = await _waiting_from_row(row)
        remove = False
        expired_by_ttl = now - row.created_at > WAITING_TTL
        if expired_by_ttl:
            remove = True
        elif is_bot_blocked(row.telegram_id):
            remove = True
        else:
            other_user = await get_user_by_id(session, row.user_id)
            if not other_user or other_user.is_banned or is_bot_blocked(other_user.telegram_id):
                remove = True
            else:
                active, _ = await is_telegram_restricted(session, other_user.telegram_id)
                if active or await get_active_match(session, row.user_id):
                    remove = True
        if remove:
            await session.delete(row)
            WAITING.pop(row.user_id, None)
            if expired_by_ttl and notify:
                expired.append(waiting)

    # Legacy shim cleanup for old tests/one-process leftovers.
    for uid, waiting in list(WAITING.items()):
        if now - waiting.created_at > WAITING_TTL:
            WAITING.pop(uid, None)
            if notify:
                expired.append(waiting)
                
    await session.commit()
    return expired


async def get_or_create_user(session: AsyncSession, tg_user: Any) -> User:
    result = await session.execute(select(User).where(User.telegram_id == int(tg_user.id)))
    user = result.scalar_one_or_none()
    if user:
        now = datetime.utcnow()
        changed = False
        username = getattr(tg_user, "username", None)
        first_name = getattr(tg_user, "first_name", None)
        language_code = getattr(tg_user, "language_code", None)
        if user.username != username:
            user.username = username
            changed = True
        if user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if user.language_code != language_code:
            user.language_code = language_code
            changed = True
        if not user.chat_mood:
            user.chat_mood = "casual"
            changed = True
        if not user.plan:
            user.plan = "free"
            changed = True
        if user.warning_count is None:
            user.warning_count = 0
            changed = True
        if user.trust_score is None:
            user.trust_score = 100
            changed = True
        if user.find_actions_count is None:
            user.find_actions_count = 0
            changed = True
        if user.plan_expires_at and user.plan_expires_at <= now and user.plan != "free":
            user.plan = "free"
            user.plan_expires_at = None
            changed = True
        if (not user.plan or user.plan == "free") and not user.is_admin:
            entitlement = (await session.execute(
                select(TelegramEntitlement).where(TelegramEntitlement.telegram_id == user.telegram_id)
            )).scalar_one_or_none()
            if entitlement and entitlement.plan != "free" and (not entitlement.plan_expires_at or entitlement.plan_expires_at > now):
                user.plan = entitlement.plan
                user.plan_expires_at = entitlement.plan_expires_at
                changed = True
        last_touch = LAST_SEEN_TOUCH.get(user.id)
        if changed or not last_touch or now - last_touch > timedelta(seconds=60):
            user.last_seen_at = now
            LAST_SEEN_TOUCH[user.id] = now
            await session.commit()
            await session.refresh(user)
        mark_bot_unblocked(user.telegram_id)
        user = await sync_user_admin_and_restriction(session, user)
        return user
    lang_code = getattr(tg_user, "language_code", None)
    # Keep Telegram language_code for analytics, but default the bot UI to DEFAULT_LANGUAGE.
    # The user can still choose uz/ru/en during onboarding. This prevents first-run/admin
    # force-join messages from unexpectedly appearing in English because of Telegram app locale.
    preferred = settings.default_language if settings.default_language in {"uz", "ru", "en"} else "uz"
    user = User(
        telegram_id=int(tg_user.id),
        username=getattr(tg_user, "username", None),
        first_name=getattr(tg_user, "first_name", None),
        language_code=lang_code,
        preferred_language=preferred,
        anon_name=make_anon_name(),
        chat_mood="casual",
        plan="free",
        is_admin=is_env_admin_id(int(tg_user.id)),
        warning_count=0,
        trust_score=100,
        onboarded=False,
        last_seen_at=datetime.utcnow(),
    )
    session.add(user)
    entitlement = (await session.execute(
        select(TelegramEntitlement).where(TelegramEntitlement.telegram_id == user.telegram_id)
    )).scalar_one_or_none()
    if entitlement and entitlement.plan != "free":
        now = datetime.utcnow()
        if not entitlement.plan_expires_at or entitlement.plan_expires_at > now:
            user.plan = entitlement.plan
            user.plan_expires_at = entitlement.plan_expires_at
    await session.commit()
    await session.refresh(user)
    mark_bot_unblocked(user.telegram_id)
    user = await sync_user_admin_and_restriction(session, user)
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_telegram(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def update_language(session: AsyncSession, user: User, lang: str) -> User:
    if lang not in {"uz", "ru", "en"}:
        lang = "uz"
    user.preferred_language = lang
    await session.commit()
    await session.refresh(user)
    return user


async def update_anon_name(session: AsyncSession, user: User, name: str) -> User:
    user.anon_name = name
    await session.commit()
    await session.refresh(user)
    return user


async def update_chat_mood(session: AsyncSession, user: User, mood: str) -> User:
    if mood not in {"casual", "deep", "funny", "movies", "support"}:
        mood = "casual"
    user.chat_mood = mood
    await session.commit()
    await session.refresh(user)
    return user


async def is_blocked_between(session: AsyncSession, a_id: int, b_id: int) -> bool:
    result = await session.execute(
        select(Block).where(
            or_(
                and_(Block.blocker_user_id == a_id, Block.blocked_user_id == b_id),
                and_(Block.blocker_user_id == b_id, Block.blocked_user_id == a_id),
            )
        )
    )
    if result.scalar_one_or_none() is not None:
        return True

    a = await get_user_by_id(session, a_id)
    b = await get_user_by_id(session, b_id)
    if not a or not b:
        return False
    telegram_result = await session.execute(
        select(TelegramBlock).where(
            or_(
                and_(TelegramBlock.blocker_telegram_id == a.telegram_id, TelegramBlock.blocked_telegram_id == b.telegram_id),
                and_(TelegramBlock.blocker_telegram_id == b.telegram_id, TelegramBlock.blocked_telegram_id == a.telegram_id),
            )
        )
    )
    return telegram_result.scalar_one_or_none() is not None


async def has_recent_report_between(session: AsyncSession, a_id: int, b_id: int) -> bool:
    cutoff = datetime.utcnow() - REPORT_MATCH_AVOID_TTL
    result = await session.execute(
        select(Report.id).where(
            Report.created_at >= cutoff,
            or_(
                and_(Report.reporter_user_id == a_id, Report.reported_user_id == b_id),
                and_(Report.reporter_user_id == b_id, Report.reported_user_id == a_id),
            )
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def can_match(session: AsyncSession, a: User, other: WaitingUser) -> bool:
    if a.id == other.user_id:
        return False
    if a.preferred_language != other.lang:
        return False
    user_mood = a.chat_mood or "casual"
    other_mood = other.mood or "casual"
    if user_mood != other_mood and user_mood != "casual" and other_mood != "casual":
        return False
    if is_bot_blocked(other.telegram_id):
        return False
    if await pair_in_rematch_cooldown(session, a.id, other.user_id):
        return False
    if await is_blocked_between(session, a.id, other.user_id):
        return False
    if await has_recent_report_between(session, a.id, other.user_id):
        return False
    other_user = await get_user_by_id(session, other.user_id)
    if not other_user or other_user.is_banned or is_bot_blocked(other_user.telegram_id):
        return False
    active_restriction, _ = await is_telegram_restricted(session, other_user.telegram_id)
    if active_restriction:
        return False
    if (a.trust_score or 100) < 10 or (other_user.trust_score or 100) < 10:
        return False
    if a.muted_until and a.muted_until > datetime.utcnow():
        return False
    if other_user.muted_until and other_user.muted_until > datetime.utcnow():
        return False
    return True


def match_score(user: User, other: WaitingUser) -> int:
    score = 0
    if user.preferred_language == other.lang:
        score += 100
    if user.chat_mood == other.mood:
        score += 30
    # Casual is compatible with every mood.
    if user.chat_mood == "casual" or other.mood == "casual":
        score += 10
    return score


async def start_waiting(session: AsyncSession, user: User, chat_id: int, waiting_message_id: int | None) -> WaitingUser | None:
    """Put user in durable queue or return a matched waiting partner.

    Uses DB-backed queue rows so restart/webhook workers can recover state. The
    local asyncio lock only reduces duplicate work in polling/dev; DB uniqueness
    is the real safety net.
    """
    async with _MATCH_LOCK:
        if is_bot_blocked(user.telegram_id):
            mark_bot_unblocked(user.telegram_id)
        await prune_waiting(session, notify=False)
        existing = (await session.execute(select(WaitingQueue).where(WaitingQueue.user_id == user.id))).scalar_one_or_none()
        if existing and datetime.utcnow() - existing.created_at <= WAITING_TTL:
            return None
        if existing:
            await session.delete(existing)
            await session.flush()
        if await get_active_match(session, user.id):
            return None

        stmt = (
            select(WaitingQueue)
            .where(WaitingQueue.user_id != user.id)
            .order_by(WaitingQueue.created_at.asc())
            .limit(100)
            .with_for_update(skip_locked=True)
        )
        rows = list((await session.execute(stmt)).scalars().all())
        candidates: list[tuple[int, WaitingUser, WaitingQueue]] = []
        for row in rows:
            other = await _waiting_from_row(row)
            if await can_match(session, user, other):
                candidates.append((match_score(user, other), other, row))
        if candidates:
            candidates.sort(key=lambda item: item[0], reverse=True)
            max_score = candidates[0][0]
            top_candidates = [candidate for candidate in candidates if candidate[0] == max_score]
            _score, partner, partner_row = secrets.choice(top_candidates)
            await session.delete(partner_row)
            await session.execute(delete(WaitingQueue).where(WaitingQueue.user_id == user.id))
            WAITING.pop(partner.user_id, None)
            WAITING.pop(user.id, None)
            await session.commit()
            return partner

        row = WaitingQueue(
            user_id=user.id,
            telegram_id=user.telegram_id,
            chat_id=int(chat_id),
            lang=user.preferred_language,
            mood=user.chat_mood or "casual",
            waiting_message_id=waiting_message_id,
        )
        session.add(row)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            # Another worker already queued this user. Treat as already waiting.
            return None
        return None


def cancel_waiting(user_id: int) -> None:
    """Legacy sync shim. Use cancel_waiting_db() in real handlers."""
    WAITING.pop(int(user_id), None)


async def cancel_waiting_db(session: AsyncSession, user_id: int) -> None:
    WAITING.pop(int(user_id), None)
    await session.execute(delete(WaitingQueue).where(WaitingQueue.user_id == int(user_id)))
    await session.commit()


async def create_match(session: AsyncSession, a_id: int, b_id: int) -> Match:
    a_id = int(a_id)
    b_id = int(b_id)
    await session.execute(delete(WaitingQueue).where(WaitingQueue.user_id.in_([a_id, b_id])))
    WAITING.pop(a_id, None)
    WAITING.pop(b_id, None)
    existing = (await session.execute(
        select(Match)
        .join(ActiveMatchParticipant, ActiveMatchParticipant.match_id == Match.id)
        .where(Match.status == "active", ActiveMatchParticipant.user_id.in_([a_id, b_id]))
        .order_by(Match.id.desc())
        .limit(1)
    )).scalar_one_or_none()
    if existing:
        return existing

    match = Match(user_a_id=a_id, user_b_id=b_id, status="active")
    session.add(match)
    await session.flush()
    session.add_all([
        ActiveMatchParticipant(match_id=match.id, user_id=a_id),
        ActiveMatchParticipant(match_id=match.id, user_id=b_id),
    ])
    try:
        await session.commit()
    except IntegrityError:
        # Another worker claimed one of the users first. Return the now-active
        # match instead of creating a duplicate active session.
        await session.rollback()
        existing = (await session.execute(
            select(Match)
            .join(ActiveMatchParticipant, ActiveMatchParticipant.match_id == Match.id)
            .where(Match.status == "active", ActiveMatchParticipant.user_id.in_([a_id, b_id]))
            .order_by(Match.id.desc())
            .limit(1)
        )).scalar_one_or_none()
        if existing:
            return existing
        raise
    await session.refresh(match)
    return match


async def get_active_match(session: AsyncSession, user_id: int) -> Match | None:
    result = await session.execute(
        select(Match)
        .join(ActiveMatchParticipant, ActiveMatchParticipant.match_id == Match.id)
        .where(Match.status == "active", ActiveMatchParticipant.user_id == int(user_id))
        .order_by(Match.id.desc())
        .limit(1)
    )
    match = result.scalar_one_or_none()
    if match:
        return match
    # Backward compatibility for active matches created before v27 migration.
    result = await session.execute(
        select(Match)
        .where(Match.status == "active")
        .where(or_(Match.user_a_id == user_id, Match.user_b_id == user_id))
        .order_by(Match.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_other_user(session: AsyncSession, match: Match, user_id: int) -> User | None:
    other_id = match.user_b_id if match.user_a_id == user_id else match.user_a_id
    return await get_user_by_id(session, other_id)


async def end_match(session: AsyncSession, match: Match, remember_pair: bool = True) -> None:
    match.status = "ended"
    match.ended_at = datetime.utcnow()
    ACTIVE.pop(match.user_a_id, None)
    ACTIVE.pop(match.user_b_id, None)
    await session.execute(delete(ActiveMatchParticipant).where(ActiveMatchParticipant.match_id == match.id))
    await session.commit()


async def save_chat(session: AsyncSession, match_id: int, sender_id: int, anon_name: str, text: str, msg_type: str = "text", is_flagged: bool = False, filter_reason: str | None = None) -> ChatMessage:
    msg = ChatMessage(match_id=match_id, sender_user_id=sender_id, anon_name_snapshot=anon_name, text=text, message_type=msg_type, is_flagged=is_flagged, filter_reason=filter_reason)
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


async def get_movie(session: AsyncSession, code: str) -> Movie | None:
    result = await session.execute(select(Movie).where(Movie.code == normalize_movie_code(code), Movie.status == "published"))
    return result.scalar_one_or_none()


async def create_movie_offer(session: AsyncSession, match: Match, offered_by: int, movie: Movie) -> MovieOffer:
    offer = MovieOffer(match_id=match.id, offered_by_user_id=offered_by, movie_id=movie.id, status="pending")
    session.add(offer)
    await session.commit()
    await session.refresh(offer)
    return offer


async def get_offer(session: AsyncSession, offer_id: int) -> MovieOffer | None:
    result = await session.execute(select(MovieOffer).where(MovieOffer.id == offer_id))
    return result.scalar_one_or_none()


async def get_movie_by_id(session: AsyncSession, movie_id: int) -> Movie | None:
    result = await session.execute(select(Movie).where(Movie.id == movie_id))
    return result.scalar_one_or_none()


async def get_recent_match_messages(session: AsyncSession, match_id: int, limit: int = 10) -> list[ChatMessage]:
    result = await session.execute(
        select(ChatMessage).where(ChatMessage.match_id == match_id).order_by(ChatMessage.id.desc()).limit(limit)
    )
    return list(reversed(result.scalars().all()))


def format_recent_messages(messages: list[ChatMessage]) -> str:
    if not messages:
        return "No recent messages saved."
    lines = []
    for msg in messages[-10:]:
        label = msg.anon_name_snapshot or f"user:{msg.sender_user_id}"
        text = (msg.text or "").replace("\n", " ")[:300]
        flag = f" [{msg.filter_reason}]" if msg.is_flagged and msg.filter_reason else ""
        lines.append(f"{msg.id} | {label}{flag}: {text}")
    return "\n".join(lines)


async def create_report(session: AsyncSession, reporter: User, reason: str, block_user: bool = False) -> Report:
    match = await get_active_match(session, reporter.id)
    reported_id = None
    recent_text = None
    if match:
        reported_id = match.user_b_id if match.user_a_id == reporter.id else match.user_a_id
        recent_text = format_recent_messages(await get_recent_match_messages(session, match.id, limit=10))
    report = Report(
        reporter_user_id=reporter.id,
        reported_user_id=reported_id,
        match_id=match.id if match else None,
        reason=reason,
        recent_messages=recent_text,
    )
    session.add(report)
    await session.flush()
    if reported_id:
        reported = await get_user_by_id(session, reported_id)
        if reported:
            await _apply_report_strike(session, reporter, reported)
    if block_user and reported_id:
        await create_block(session, reporter.id, reported_id, reason=reason, commit=False)
    await session.commit()
    await session.refresh(report)
    return report


async def _apply_report_strike(session: AsyncSession, reporter: User, reported: User) -> None:
    reported.trust_score = max(0, (reported.trust_score or 100) - 10)
    cutoff = datetime.utcnow() - timedelta(days=7)
    existing_recent = (await session.execute(
        select(ReportStrike).where(
            ReportStrike.reported_telegram_id == reported.telegram_id,
            ReportStrike.reporter_telegram_id == reporter.telegram_id,
            ReportStrike.created_at >= cutoff,
        )
    )).scalar_one_or_none()
    if not existing_recent:
        session.add(ReportStrike(reported_telegram_id=reported.telegram_id, reporter_telegram_id=reporter.telegram_id))
        await session.flush()
    strike_count = (await session.execute(
        select(func.count(ReportStrike.id)).where(
            ReportStrike.reported_telegram_id == reported.telegram_id,
            ReportStrike.created_at >= cutoff,
        )
    )).scalar_one()
    if int(strike_count) >= 3 and not reported.is_admin:
        restriction = await get_restriction(session, reported.telegram_id)
        if not restriction:
            restriction = TelegramRestriction(telegram_id=reported.telegram_id)
            session.add(restriction)
        restriction.report_strikes = int(strike_count)
        restriction.banned_until = datetime.utcnow() + timedelta(hours=2)
        restriction.reason = "3 reports"
        restriction.updated_at = datetime.utcnow()
        reported.is_banned = True
        reported.ban_reason = "3 reports"
        session.add(BanHistory(user_id=reported.id, admin_user_id=None, action="auto_ban_2h", reason="3 reports", starts_at=datetime.utcnow(), ends_at=restriction.banned_until))


async def create_room_report(session: AsyncSession, reporter: User, reported: User, room: Room, reason: str = "room_report") -> Report:
    recent_messages = (await session.execute(
        select(RoomMessage)
        .where(RoomMessage.room_id == room.id)
        .order_by(RoomMessage.id.desc())
        .limit(10)
    )).scalars().all()
    formatted = "\n".join(
        f"{m.anon_name_snapshot}: {m.text}" for m in reversed(list(recent_messages))
    )
    report = Report(
        reporter_user_id=reporter.id,
        reported_user_id=reported.id,
        match_id=None,
        reason=reason,
        recent_messages=formatted,
    )
    session.add(report)
    await session.flush()
    await _apply_report_strike(session, reporter, reported)
    await session.commit()
    await session.refresh(report)
    return report

async def create_block(session: AsyncSession, blocker_id: int, blocked_id: int, reason: str | None = None, commit: bool = True) -> Block:
    result = await session.execute(
        select(Block).where(Block.blocker_user_id == blocker_id, Block.blocked_user_id == blocked_id)
    )
    block = result.scalar_one_or_none()
    if not block:
        block = Block(blocker_user_id=blocker_id, blocked_user_id=blocked_id, reason=reason)
        session.add(block)

    blocker = await get_user_by_id(session, blocker_id)
    blocked = await get_user_by_id(session, blocked_id)
    if blocker and blocked:
        tb_result = await session.execute(
            select(TelegramBlock).where(
                TelegramBlock.blocker_telegram_id == blocker.telegram_id,
                TelegramBlock.blocked_telegram_id == blocked.telegram_id,
            )
        )
        telegram_block = tb_result.scalar_one_or_none()
        if not telegram_block:
            session.add(TelegramBlock(
                blocker_telegram_id=blocker.telegram_id,
                blocked_telegram_id=blocked.telegram_id,
                reason=reason,
            ))
    if commit:
        await session.commit()
        await session.refresh(block)
    return block


async def grant_plan(session: AsyncSession, telegram_id: int, plan: str, days: int | None = None) -> User | None:
    if plan not in {"free", "plus", "pro"}:
        plan = "free"
    user = await get_user_by_telegram(session, telegram_id)
    if not user:
        return None
    user.plan = plan
    if plan == "free":
        user.plan_expires_at = None
    else:
        user.plan_expires_at = datetime.utcnow() + timedelta(days=days or 30)
    entitlement = (await session.execute(
        select(TelegramEntitlement).where(TelegramEntitlement.telegram_id == user.telegram_id)
    )).scalar_one_or_none()
    if not entitlement:
        entitlement = TelegramEntitlement(telegram_id=user.telegram_id)
        session.add(entitlement)
    entitlement.plan = user.plan
    entitlement.plan_expires_at = user.plan_expires_at
    entitlement.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(user)
    return user


def plan_rank(plan: str | None) -> int:
    return {"free": 0, "plus": 1, "pro": 2}.get(plan or "free", 0)


def plan_name(user: User) -> str:
    return user.plan or "free"


def is_premium(user: User) -> bool:
    return bool(user.is_admin or plan_rank(user.plan) >= 1)


def daily_skip_limit(user: User) -> int:
    if user.is_admin:
        return settings.pro_daily_skips
    if user.plan == "pro":
        return settings.pro_daily_skips
    if user.plan == "plus":
        return settings.plus_daily_skips
    return settings.free_daily_skips


def can_join_rooms(user: User) -> bool:
    # Public rooms can be used as a free taste of the product when enabled.
    return bool(user.is_admin or settings.allow_free_room_join or plan_rank(user.plan) >= 1)


def can_join_private_rooms(user: User) -> bool:
    # Private/invite-code rooms stay a Plus/Pro hosting perk.
    return bool(user.is_admin or plan_rank(user.plan) >= 1)


def can_edit_name_after_onboarding(user: User) -> bool:
    return bool(user.is_admin or plan_rank(user.plan) >= 1)


def today_key() -> str:
    return date.today().isoformat()


async def get_usage_today(session: AsyncSession, user: User) -> UsageDaily:
    user_id = model_id(user)
    key = today_key()
    result = await session.execute(select(UsageDaily).where(UsageDaily.user_id == user_id, UsageDaily.date == key))
    usage = result.scalar_one_or_none()
    if usage:
        return usage
    usage = UsageDaily(user_id=user_id, date=key, skips_count=0, movie_unlocks_count=0, messages_count=0)
    session.add(usage)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        usage = (await session.execute(select(UsageDaily).where(UsageDaily.user_id == user_id, UsageDaily.date == key))).scalar_one()
        return usage
    await session.refresh(usage)
    return usage


async def can_skip_today(session: AsyncSession, user: User) -> tuple[bool, int, int]:
    usage = await get_usage_today(session, user)
    limit = daily_skip_limit(user)
    return usage.skips_count < limit, usage.skips_count, limit


async def record_skip(session: AsyncSession, user: User) -> UsageDaily:
    usage = await get_usage_today(session, user)
    await session.execute(
        update(UsageDaily)
        .where(UsageDaily.id == usage.id)
        .values(skips_count=UsageDaily.skips_count + 1, updated_at=datetime.utcnow())
    )
    await session.commit()
    await session.refresh(usage)
    return usage


def month_key() -> str:
    return date.today().strftime("%Y-%m")


async def get_usage_month(session: AsyncSession, user: User) -> UsageMonthly:
    user_id = model_id(user)
    key = month_key()
    result = await session.execute(select(UsageMonthly).where(UsageMonthly.user_id == user_id, UsageMonthly.month == key))
    usage = result.scalar_one_or_none()
    if usage:
        return usage

    # Preserve existing daily counters when upgrading from pre-v27 installs.
    prefix = f"{key}%"
    used = int((await session.execute(
        select(func.coalesce(func.sum(UsageDaily.movie_unlocks_count), 0)).where(
            UsageDaily.user_id == user_id, UsageDaily.date.like(prefix)
        )
    )).scalar_one() or 0)
    usage = UsageMonthly(user_id=user_id, month=key, movie_unlocks_count=used)
    session.add(usage)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        usage = (await session.execute(select(UsageMonthly).where(UsageMonthly.user_id == user_id, UsageMonthly.month == key))).scalar_one()
        return usage
    await session.refresh(usage)
    return usage


async def movie_unlocks_this_month(session: AsyncSession, user: User) -> int:
    usage = await get_usage_month(session, user)
    return int(usage.movie_unlocks_count or 0)


async def can_unlock_movie(session: AsyncSession, user: User) -> tuple[bool, int, int, str]:
    if user.is_admin:
        return True, 0, settings.pro_daily_movie_unlocks, "daily"
    if user.plan == "plus":
        used = await movie_unlocks_this_month(session, user)
        limit = settings.plus_monthly_movie_unlocks
        return used < limit, used, limit, "monthly"
    usage = await get_usage_today(session, user)
    limit = settings.pro_daily_movie_unlocks if user.plan == "pro" else settings.free_daily_movie_unlocks
    return usage.movie_unlocks_count < limit, usage.movie_unlocks_count, limit, "daily"


async def consume_movie_unlock(session: AsyncSession, user: User) -> tuple[bool, int, int, str]:
    """Atomically reserve one movie unlock for the user.

    Returns (ok, used_before, limit, period). This replaces the older
    check-then-increment pattern that could overrun limits under duplicate
    callbacks or multi-worker webhook delivery.
    """
    user_id = model_id(user)
    fresh_user = await get_user_by_id(session, user_id)
    if fresh_user is not None:
        user = fresh_user
    if user.is_admin:
        return True, 0, settings.pro_daily_movie_unlocks, "daily"

    if user.plan == "plus":
        usage = await get_usage_month(session, user)
        limit = settings.plus_monthly_movie_unlocks
        used_before = int(usage.movie_unlocks_count or 0)
        result = await session.execute(
            update(UsageMonthly)
            .where(UsageMonthly.id == usage.id, UsageMonthly.movie_unlocks_count < limit)
            .values(movie_unlocks_count=UsageMonthly.movie_unlocks_count + 1, updated_at=datetime.utcnow())
        )
        if (result.rowcount or 0) != 1:
            await session.rollback()
            usage = await get_usage_month(session, user)
            return False, int(usage.movie_unlocks_count or 0), limit, "monthly"
        await session.commit()
        # Keep daily analytics in sync, but make the monthly row the source of truth.
        try:
            daily = await get_usage_today(session, user)
            await session.execute(
                update(UsageDaily)
                .where(UsageDaily.id == daily.id)
                .values(movie_unlocks_count=UsageDaily.movie_unlocks_count + 1, updated_at=datetime.utcnow())
            )
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.warning("Daily movie unlock analytics update failed user_id=%s: %s", user_id, exc, exc_info=True)
        return True, used_before, limit, "monthly"

    usage = await get_usage_today(session, user)
    limit = settings.pro_daily_movie_unlocks if user.plan == "pro" else settings.free_daily_movie_unlocks
    used_before = int(usage.movie_unlocks_count or 0)
    result = await session.execute(
        update(UsageDaily)
        .where(UsageDaily.id == usage.id, UsageDaily.movie_unlocks_count < limit)
        .values(movie_unlocks_count=UsageDaily.movie_unlocks_count + 1, updated_at=datetime.utcnow())
    )
    if (result.rowcount or 0) != 1:
        await session.rollback()
        usage = await get_usage_today(session, user)
        return False, int(usage.movie_unlocks_count or 0), limit, "daily"
    await session.commit()
    return True, used_before, limit, "daily"


async def refund_movie_unlock(session: AsyncSession, user: User) -> None:
    """Best-effort refund if Telegram delivery fails before a user receives a movie."""
    user_id = model_id(user)
    fresh_user = await get_user_by_id(session, user_id)
    if fresh_user is not None:
        user = fresh_user
    if user.is_admin:
        return
    try:
        if user.plan == "plus":
            usage = await get_usage_month(session, user)
            await session.execute(
                update(UsageMonthly)
                .where(UsageMonthly.id == usage.id, UsageMonthly.movie_unlocks_count > 0)
                .values(movie_unlocks_count=UsageMonthly.movie_unlocks_count - 1, updated_at=datetime.utcnow())
            )
        daily = await get_usage_today(session, user)
        await session.execute(
            update(UsageDaily)
            .where(UsageDaily.id == daily.id, UsageDaily.movie_unlocks_count > 0)
            .values(movie_unlocks_count=UsageDaily.movie_unlocks_count - 1, updated_at=datetime.utcnow())
        )
        await session.commit()
    except Exception as exc:
        await session.rollback()
        logger.warning("Movie unlock refund failed user_id=%s: %s", user_id, exc, exc_info=True)


async def record_movie_unlock(session: AsyncSession, user: User) -> UsageDaily:
    # Backward-compatible wrapper. New handlers should use consume_movie_unlock().
    await consume_movie_unlock(session, user)
    return await get_usage_today(session, user)


async def usage_summary(session: AsyncSession, user: User) -> dict:
    usage = await get_usage_today(session, user)
    movie_ok, movie_used, movie_limit, movie_period = await can_unlock_movie(session, user)
    return {
        "plan": user.plan or "free",
        "expires_at": user.plan_expires_at,
        "skips_used": usage.skips_count,
        "skips_limit": daily_skip_limit(user),
        "movie_used": movie_used,
        "movie_limit": movie_limit,
        "movie_period": movie_period,
        "movie_ok": movie_ok,
    }


def room_limit_for(user: User) -> int:
    if user.plan == "pro" or user.is_admin:
        return 14
    if user.plan == "plus":
        return 7
    return 0


async def get_active_room(session: AsyncSession, user_id: int) -> Room | None:
    result = await session.execute(
        select(Room).join(RoomMember, RoomMember.room_id == Room.id).where(
            Room.status == "open",
            RoomMember.user_id == user_id,
            RoomMember.left_at.is_(None),
        ).order_by(RoomMember.id.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def room_member_count(session: AsyncSession, room_id: int) -> int:
    result = await session.execute(
        select(func.count(RoomMember.id)).where(RoomMember.room_id == room_id, RoomMember.left_at.is_(None))
    )
    return int(result.scalar_one())


async def create_room(session: AsyncSession, host: User, title: str | None = None, is_private: bool = False) -> Room:
    limit = room_limit_for(host)
    if limit <= 0:
        raise PermissionError("premium_required")
    clean_title = (title or "").strip()[:80]
    if not clean_title:
        clean_title = f"{host.anon_name}'s room"
    code = make_invite_code()
    # Very small collision guard for local SQLite use.
    for _ in range(8):
        existing = (await session.execute(select(Room).where(Room.invite_code == code))).scalar_one_or_none()
        if not existing:
            break
        code = make_invite_code()
    room = Room(
        host_user_id=host.id,
        title=clean_title,
        language=host.preferred_language,
        mood=host.chat_mood or "casual",
        max_members=limit,
        invite_code=code,
        status="open",
        is_private=is_private,
        last_activity_at=datetime.utcnow(),
    )
    session.add(room)
    await session.flush()
    member = RoomMember(room_id=room.id, user_id=host.id, anon_name_snapshot=host.anon_name, role="host")
    session.add(member)
    await session.commit()
    await session.refresh(room)
    return room


async def list_public_rooms(session: AsyncSession, user: User, limit: int = 8) -> list[tuple[Room, int]]:
    """Return visible public rooms with current member counts for a user.

    Public rooms are deliberately shown as a choice list instead of silently
    auto-joining. This keeps the room UX clear when several public rooms exist.
    """
    result = await session.execute(
        select(Room)
        .where(Room.status == "open", Room.is_private.is_(False), Room.language == user.preferred_language)
        .order_by(Room.last_activity_at.desc(), Room.id.desc())
        .limit(max(limit * 3, limit))
    )
    visible: list[tuple[Room, int]] = []
    for room in result.scalars().all():
        if room.host_user_id == user.id:
            continue
        already = (await session.execute(
            select(RoomMember).where(RoomMember.room_id == room.id, RoomMember.user_id == user.id, RoomMember.left_at.is_(None))
        )).scalar_one_or_none()
        if already:
            visible.append((room, await room_member_count(session, room.id)))
            break
        count = await room_member_count(session, room.id)
        if count >= room.max_members:
            continue
        visible.append((room, count))
        if len(visible) >= limit:
            break
    return visible


async def find_public_room(session: AsyncSession, user: User) -> Room | None:
    rooms = await list_public_rooms(session, user, limit=20)
    return rooms[0][0] if rooms else None


async def join_room(session: AsyncSession, user: User, room: Room) -> RoomMember:
    if room.is_private:
        if not can_join_private_rooms(user):
            raise PermissionError("premium_required")
    elif not can_join_rooms(user):
        raise PermissionError("premium_required")
    locked_room = (await session.execute(
        select(Room).where(Room.id == room.id, Room.status == "open").with_for_update()
    )).scalar_one_or_none()
    if not locked_room:
        raise ValueError("room_closed")
    existing_any = (await session.execute(
        select(RoomMember).where(RoomMember.room_id == room.id, RoomMember.user_id == user.id)
    )).scalar_one_or_none()
    if existing_any and existing_any.left_at is None:
        return existing_any
    count = await room_member_count(session, room.id)
    if count >= locked_room.max_members:
        raise ValueError("room_full")
    if existing_any:
        existing_any.left_at = None
        existing_any.anon_name_snapshot = user.anon_name
        existing_any.is_muted = False
        member = existing_any
    else:
        member = RoomMember(room_id=room.id, user_id=user.id, anon_name_snapshot=user.anon_name, role="member")
        session.add(member)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        member = (await session.execute(
            select(RoomMember).where(RoomMember.room_id == room.id, RoomMember.user_id == user.id)
        )).scalar_one()
        return member
    await session.refresh(member)
    return member


async def leave_room(session: AsyncSession, user: User, room: Room) -> list[User]:
    result = await session.execute(select(RoomMember).where(RoomMember.room_id == room.id, RoomMember.user_id == user.id, RoomMember.left_at.is_(None)))
    member = result.scalar_one_or_none()
    if member:
        member.left_at = datetime.utcnow()
    ACTIVE_ROOM.pop(user.id, None)
    remaining = await get_room_users(session, room.id, exclude_user_id=user.id)
    if not remaining:
        room.status = "closed"
        room.closed_at = datetime.utcnow()
    await session.commit()
    return remaining


async def get_room_users(session: AsyncSession, room_id: int, exclude_user_id: int | None = None) -> list[User]:
    stmt = select(User).join(RoomMember, RoomMember.user_id == User.id).where(RoomMember.room_id == room_id, RoomMember.left_at.is_(None))
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_room_members(session: AsyncSession, room_id: int) -> list[RoomMember]:
    result = await session.execute(select(RoomMember).where(RoomMember.room_id == room_id, RoomMember.left_at.is_(None)).order_by(RoomMember.id.asc()))
    return list(result.scalars().all())


async def save_room_chat(session: AsyncSession, room_id: int, sender_id: int, anon_name: str, text: str) -> RoomMessage:
    msg = RoomMessage(room_id=room_id, sender_user_id=sender_id, anon_name_snapshot=anon_name, text=text)
    room = (await session.execute(select(Room).where(Room.id == room_id))).scalar_one_or_none()
    if room:
        room.last_activity_at = datetime.utcnow()
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


async def close_inactive_rooms(session: AsyncSession, hours: int = 6) -> int:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    result = await session.execute(select(Room).where(Room.status == "open", Room.last_activity_at <= cutoff))
    rooms = result.scalars().all()
    count = 0
    for room in rooms:
        room.status = "closed"
        room.closed_at = datetime.utcnow()
        count += 1
    if count:
        await session.commit()
    return count


async def get_room_by_invite(session: AsyncSession, code: str) -> Room | None:
    result = await session.execute(select(Room).where(Room.invite_code == code.strip().upper(), Room.status == "open"))
    return result.scalar_one_or_none()


async def get_room_member(session: AsyncSession, room_id: int, user_id: int) -> RoomMember | None:
    result = await session.execute(
        select(RoomMember).where(RoomMember.room_id == room_id, RoomMember.user_id == user_id, RoomMember.left_at.is_(None))
    )
    return result.scalar_one_or_none()


async def is_room_host(session: AsyncSession, room: Room, user_id: int) -> bool:
    if room.host_user_id == user_id:
        return True
    member = await get_room_member(session, room.id, user_id)
    return bool(member and member.role == "host")


async def set_room_member_mute(session: AsyncSession, room: Room, host: User, target_user_id: int, muted: bool) -> RoomMember | None:
    if not await is_room_host(session, room, host.id):
        raise PermissionError("host_required")
    if target_user_id == host.id:
        raise ValueError("cannot_target_self")
    member = await get_room_member(session, room.id, target_user_id)
    if not member:
        return None
    member.is_muted = muted
    await session.commit()
    await session.refresh(member)
    return member


async def kick_room_member(session: AsyncSession, room: Room, host: User, target_user_id: int) -> RoomMember | None:
    if not await is_room_host(session, room, host.id):
        raise PermissionError("host_required")
    if target_user_id == host.id:
        raise ValueError("cannot_target_self")
    member = await get_room_member(session, room.id, target_user_id)
    if not member:
        return None
    member.left_at = datetime.utcnow()
    ACTIVE_ROOM.pop(target_user_id, None)
    await session.commit()
    await session.refresh(member)
    return member


async def create_room_movie_offer(session: AsyncSession, room: Room, offered_by: User, movie: Movie) -> RoomMovieOffer:
    offer = RoomMovieOffer(
        room_id=room.id,
        offered_by_user_id=offered_by.id,
        movie_id=movie.id,
        status="voting",
        yes_votes_count=1,
        no_votes_count=0,
    )
    session.add(offer)
    await session.flush()
    vote = RoomMovieVote(offer_id=offer.id, user_id=offered_by.id, vote="yes")
    session.add(vote)
    room.last_activity_at = datetime.utcnow()
    await session.commit()
    await session.refresh(offer)
    return offer


async def get_room_offer(session: AsyncSession, offer_id: int) -> RoomMovieOffer | None:
    result = await session.execute(select(RoomMovieOffer).where(RoomMovieOffer.id == offer_id))
    return result.scalar_one_or_none()


async def vote_room_movie_offer(session: AsyncSession, offer: RoomMovieOffer, user: User, vote_value: str) -> tuple[RoomMovieOffer, str]:
    if vote_value not in {"yes", "no"}:
        vote_value = "no"
    if offer.status != "voting":
        return offer, offer.status
    existing = (await session.execute(select(RoomMovieVote).where(RoomMovieVote.offer_id == offer.id, RoomMovieVote.user_id == user.id))).scalar_one_or_none()
    if existing:
        existing.vote = vote_value
    else:
        session.add(RoomMovieVote(offer_id=offer.id, user_id=user.id, vote=vote_value))
    await session.flush()
    yes = (await session.execute(select(func.count(RoomMovieVote.id)).where(RoomMovieVote.offer_id == offer.id, RoomMovieVote.vote == "yes"))).scalar_one()
    no = (await session.execute(select(func.count(RoomMovieVote.id)).where(RoomMovieVote.offer_id == offer.id, RoomMovieVote.vote == "no"))).scalar_one()
    total = await room_member_count(session, offer.room_id)
    offer.yes_votes_count = int(yes)
    offer.no_votes_count = int(no)
    resolved = "voting"
    if total > 0 and offer.yes_votes_count > total / 2:
        offer.status = "accepted"
        offer.resolved_at = datetime.utcnow()
        resolved = "accepted"
    elif total > 0 and offer.no_votes_count >= (total + 1) // 2:
        offer.status = "rejected"
        offer.resolved_at = datetime.utcnow()
        resolved = "rejected"
    room = (await session.execute(select(Room).where(Room.id == offer.room_id))).scalar_one_or_none()
    if room:
        room.last_activity_at = datetime.utcnow()
    await session.commit()
    await session.refresh(offer)
    return offer, resolved



# v14 strong moderation helpers
async def add_warning(session: AsyncSession, user: User, reason: str, message_text: str | None = None) -> tuple[User, bool]:
    warn = UserWarning(user_id=user.id, reason=reason, message_text=(message_text or "")[:1500])
    session.add(warn)
    user.warning_count = (user.warning_count or 0) + 1
    user.trust_score = max(0, (user.trust_score or 100) - (10 if reason == "bad_word" else 5))
    auto_banned = False
    if user.warning_count >= 3 and not user.is_admin:
        restriction = await get_restriction(session, user.telegram_id)
        if not restriction:
            restriction = TelegramRestriction(telegram_id=user.telegram_id)
            session.add(restriction)
        restriction.warning_strikes = (restriction.warning_strikes or 0) + 1
        restriction.banned_until = datetime.utcnow() + timedelta(hours=2)
        restriction.reason = "3 warnings"
        restriction.updated_at = datetime.utcnow()
        user.is_banned = True
        user.ban_reason = "3 warnings"
        auto_banned = True
        session.add(BanHistory(user_id=user.id, admin_user_id=None, action="auto_ban_2h", reason="3 warnings", starts_at=datetime.utcnow(), ends_at=restriction.banned_until))
    await session.commit()
    await session.refresh(user)
    return user, auto_banned


def is_user_muted(user: User) -> bool:
    return bool(user.muted_until and user.muted_until > datetime.utcnow())


def muted_remaining_text(user: User) -> str:
    if not is_user_muted(user):
        return ""
    delta = user.muted_until - datetime.utcnow()
    minutes = max(1, int(delta.total_seconds() // 60))
    if minutes >= 60:
        return f"{minutes // 60}h {minutes % 60}m"
    return f"{minutes}m"


async def mute_user(session: AsyncSession, user: User, hours: int, reason: str, admin: User | None = None) -> User:
    hours = max(1, min(int(hours), 24 * 30))
    user.muted_until = datetime.utcnow() + timedelta(hours=hours)
    user.trust_score = max(0, (user.trust_score or 100) - 15)
    session.add(BanHistory(user_id=user.id, admin_user_id=admin.id if admin else None, action="mute", reason=reason, starts_at=datetime.utcnow(), ends_at=user.muted_until))
    await session.commit()
    await session.refresh(user)
    return user


async def unmute_user(session: AsyncSession, user: User, admin: User | None = None, reason: str = "unmute") -> User:
    user.muted_until = None
    session.add(BanHistory(user_id=user.id, admin_user_id=admin.id if admin else None, action="unmute", reason=reason, starts_at=datetime.utcnow(), ends_at=None))
    await session.commit()
    await session.refresh(user)
    return user


async def ban_user(session: AsyncSession, user: User, reason: str, admin: User | None = None) -> User:
    user.is_banned = True
    user.ban_reason = reason
    user.trust_score = max(0, (user.trust_score or 100) - 40)
    session.add(BanHistory(user_id=user.id, admin_user_id=admin.id if admin else None, action="ban", reason=reason, starts_at=datetime.utcnow(), ends_at=None))
    await session.commit()
    await session.refresh(user)
    return user


async def unban_user(session: AsyncSession, user: User, admin: User | None = None) -> User:
    user.is_banned = False
    user.ban_reason = None
    session.add(BanHistory(user_id=user.id, admin_user_id=admin.id if admin else None, action="unban", reason="unban", starts_at=datetime.utcnow(), ends_at=None))
    await session.commit()
    await session.refresh(user)
    return user


async def get_ban_history(session: AsyncSession, user_id: int, limit: int = 10) -> list[BanHistory]:
    result = await session.execute(select(BanHistory).where(BanHistory.user_id == user_id).order_by(BanHistory.id.desc()).limit(limit))
    return list(result.scalars().all())


async def review_report(session: AsyncSession, report: Report, admin: User, action: str) -> tuple[Report, str]:
    action = (action or "").strip().lower()
    if action not in {"dismiss", "warn", "mute24", "ban", "block"}:
        return report, "invalid_action"
    target = await get_user_by_id(session, report.reported_user_id) if report.reported_user_id else None
    if action == "dismiss":
        report.status = "dismissed"
    elif not target:
        return report, "target_not_found"
    elif action == "warn":
        await add_warning(session, target, f"report:{report.reason}", report.recent_messages)
        report.status = "action_taken"
    elif action == "mute24":
        await mute_user(session, target, 24, f"report:{report.reason}", admin=admin)
        report.status = "action_taken"
    elif action == "ban":
        await ban_user(session, target, f"report:{report.reason}", admin=admin)
        report.status = "action_taken"
    elif action == "block":
        if report.reporter_user_id and report.reported_user_id:
            await create_block(session, report.reporter_user_id, report.reported_user_id, reason=f"report:{report.reason}", commit=False)
        report.status = "action_taken"
    report.reviewed_by_admin_id = admin.id
    report.reviewed_at = datetime.utcnow()
    report.action_taken = action
    await session.commit()
    await session.refresh(report)
    return report, "ok"

# v12 Telegram Stars payment helpers
VALID_PAYMENT_DURATIONS = {1, 3, 6, 12}


def star_price(plan: str, months: int) -> int:
    key = f"{plan}_{months}m_stars"
    if plan not in {"plus", "pro"} or months not in VALID_PAYMENT_DURATIONS:
        raise ValueError("invalid_plan_or_duration")
    return int(getattr(settings, key))


def payment_days(months: int) -> int:
    return int(months) * 30


def make_invoice_payload(user: User, plan: str, months: int) -> str:
    nonce = secrets.token_urlsafe(12)
    return f"ctb:v12:{user.id}:{plan}:{months}:{nonce}"


def parse_invoice_payload(payload: str) -> dict[str, Any] | None:
    parts = (payload or "").split(":")
    if len(parts) != 6 or parts[0] != "ctb" or parts[1] != "v12":
        return None
    try:
        return {"user_id": int(parts[2]), "plan": parts[3], "months": int(parts[4]), "nonce": parts[5]}
    except ValueError:
        return None


async def create_payment_invoice(session: AsyncSession, user: User, plan: str, months: int) -> Payment:
    stars = star_price(plan, months)
    cutoff = datetime.utcnow() - timedelta(minutes=15)
    existing = (await session.execute(
        select(Payment).where(
            Payment.user_id == user.id,
            Payment.plan == plan,
            Payment.duration_months == months,
            Payment.status == "pending",
            Payment.created_at >= cutoff,
        ).order_by(Payment.id.desc()).limit(1)
    )).scalar_one_or_none()
    if existing:
        return existing
    payload = make_invoice_payload(user, plan, months)
    payment = Payment(
        user_id=user.id,
        plan=plan,
        duration_months=months,
        stars_amount=stars,
        invoice_payload=payload,
        status="pending",
    )
    session.add(payment)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return (await session.execute(select(Payment).where(Payment.invoice_payload == payload))).scalar_one()
    await session.refresh(payment)
    return payment


async def get_payment_by_payload(session: AsyncSession, payload: str) -> Payment | None:
    result = await session.execute(select(Payment).where(Payment.invoice_payload == payload))
    return result.scalar_one_or_none()


async def mark_payment_status(session: AsyncSession, payment: Payment, status: str, raw_payload: str | None = None) -> Payment:
    payment.status = status
    payment.updated_at = datetime.utcnow()
    if raw_payload is not None:
        payment.raw_payload = raw_payload
    await session.commit()
    await session.refresh(payment)
    return payment


async def complete_payment(session: AsyncSession, payment: Payment, charge_id: str | None = None, raw_payload: str | None = None) -> User | None:
    """Idempotently activate a paid plan exactly once.

    Telegram may deliver the same successful_payment update more than once, and
    webhook deployments may process duplicate updates concurrently. The payment
    row is therefore claimed with a conditional UPDATE from pending -> succeeded
    (or mock). Only the worker that changes exactly one pending row extends the
    subscription. Replays return the already-activated user without adding days.
    """
    target_status = "succeeded" if charge_id else "mock"

    if charge_id:
        existing = (await session.execute(
            select(Payment).where(Payment.telegram_payment_charge_id == charge_id)
        )).scalar_one_or_none()
        if existing and existing.id != payment.id:
            return await get_user_by_id(session, existing.user_id)

    current = (await session.execute(select(Payment).where(Payment.id == payment.id))).scalar_one_or_none()
    if not current:
        return None
    if current.status in {"succeeded", "mock"}:
        return await get_user_by_id(session, current.user_id)
    if current.status != "pending":
        return None

    user = await get_user_by_id(session, current.user_id)
    if not user:
        return None

    values: dict[str, Any] = {
        "status": target_status,
        "raw_payload": raw_payload,
        "updated_at": datetime.utcnow(),
    }
    if charge_id:
        values["telegram_payment_charge_id"] = charge_id

    result = await session.execute(
        update(Payment)
        .where(Payment.id == current.id, Payment.status == "pending")
        .values(**values)
    )
    if (result.rowcount or 0) != 1:
        await session.rollback()
        return await get_user_by_id(session, current.user_id)

    # Extend active subscription from current expiry if possible, otherwise start from now.
    now = datetime.utcnow()
    base = user.plan_expires_at if user.plan_expires_at and user.plan_expires_at > now else now
    user.plan = current.plan
    user.plan_expires_at = base + timedelta(days=payment_days(current.duration_months))

    entitlement = (await session.execute(
        select(TelegramEntitlement).where(TelegramEntitlement.telegram_id == user.telegram_id)
    )).scalar_one_or_none()
    if not entitlement:
        entitlement = TelegramEntitlement(telegram_id=user.telegram_id)
        session.add(entitlement)
    entitlement.plan = current.plan
    entitlement.plan_expires_at = user.plan_expires_at
    entitlement.updated_at = datetime.utcnow()

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        if charge_id:
            existing = (await session.execute(
                select(Payment).where(Payment.telegram_payment_charge_id == charge_id)
            )).scalar_one_or_none()
            if existing:
                return await get_user_by_id(session, existing.user_id)
        raise

    refreshed = await get_user_by_id(session, user.id)
    return refreshed


async def mock_activate_plan(session: AsyncSession, user: User, plan: str, months: int) -> User:
    payment = await create_payment_invoice(session, user, plan, months)
    return await complete_payment(session, payment, charge_id=None, raw_payload="mock") or user

# v13 movie admin/publishing helpers
LEGAL_SOURCE_TYPES = {"public_domain", "licensed", "own_content", "external_legal_link"}
MOVIE_STATUSES = {"draft", "published", "hidden"}


def normalize_movie_code(code: str) -> str:
    return (code or "").strip().upper().replace(" ", "-")[:32]


def normalize_watch_start_arg(arg: str) -> str:
    raw = (arg or "").strip()
    if raw.lower().startswith("watch_"):
        raw = raw[6:]
    return normalize_movie_code(raw)


async def save_pending_watch_intent(session: AsyncSession, telegram_id: int, code: str) -> None:
    code = normalize_watch_start_arg(code)
    if not code:
        return
    existing = (await session.execute(
        select(PendingWatchIntent).where(PendingWatchIntent.telegram_id == int(telegram_id))
    )).scalar_one_or_none()
    now = datetime.utcnow()
    if existing:
        existing.code = code
        existing.updated_at = now
    else:
        session.add(PendingWatchIntent(telegram_id=int(telegram_id), code=code, created_at=now, updated_at=now))
    await session.commit()


async def pop_pending_watch_intent(session: AsyncSession, telegram_id: int) -> str:
    existing = (await session.execute(
        select(PendingWatchIntent).where(PendingWatchIntent.telegram_id == int(telegram_id))
    )).scalar_one_or_none()
    if not existing:
        return ""
    code = existing.code
    await session.delete(existing)
    await session.commit()
    return code


async def generate_movie_code(session: AsyncSession, prefix: str = "KINO") -> str:
    prefix = normalize_movie_code(prefix or "KINO").replace("-", "")[:8] or "KINO"
    for _ in range(50):
        code = f"{prefix}-{secrets.randbelow(9000) + 1000}"
        existing = (await session.execute(select(Movie).where(Movie.code == code))).scalar_one_or_none()
        if not existing:
            return code
    raise RuntimeError("could_not_generate_unique_code")


async def get_movie_any(session: AsyncSession, code: str) -> Movie | None:
    result = await session.execute(select(Movie).where(Movie.code == normalize_movie_code(code)))
    return result.scalar_one_or_none()


async def list_movies(session: AsyncSession, status: str | None = None, limit: int = 200) -> list[Movie]:
    query = select(Movie).order_by(Movie.id.asc()).limit(limit)
    if status in MOVIE_STATUSES:
        query = select(Movie).where(Movie.status == status).order_by(Movie.id.asc()).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_movie_by_number(session: AsyncSession, number: int) -> Movie | None:
    if number < 1:
        return None
    result = await session.execute(
        select(Movie).order_by(Movie.id.asc()).offset(number - 1).limit(1)
    )
    return result.scalar_one_or_none()


def format_numbered_movies(movies: list[Movie]) -> str:
    if not movies:
        return ""
    return "\n".join(f"{i}. {m.code} — {m.title} [{m.status}]" for i, m in enumerate(movies, 1))


def validate_movie_publishable(movie: Movie) -> list[str]:
    errors: list[str] = []
    if not (movie.title or "").strip():
        errors.append("title")
    if not normalize_movie_code(movie.code):
        errors.append("code")
    if not ((movie.legal_watch_url or "").strip() or (movie.video_file_id or "").strip()):
        errors.append("legal_watch_url_or_video_file_id")
    if (movie.source_type or "") not in LEGAL_SOURCE_TYPES:
        errors.append("source_type")
    if not (movie.source_note or "").strip():
        errors.append("source_note")
    return errors


async def create_admin_movie(
    session: AsyncSession,
    admin: User,
    *,
    code: str,
    title: str,
    description: str = "",
    legal_watch_url: str = "",
    video_file_id: str = "",
    poster_file_id: str = "",
    source_type: str = "",
    source_note: str = "",
    year: int | None = None,
    genres: str = "",
    language: str = "uz",
    subtitle_language: str | None = None,
    duration_minutes: int | None = None,
    status: str = "draft",
) -> Movie:
    code = normalize_movie_code(code)
    if not code or code == "AUTO":
        code = await generate_movie_code(session)
    existing = await get_movie_any(session, code)
    if existing:
        raise ValueError("duplicate_code")
    if source_type and source_type not in LEGAL_SOURCE_TYPES:
        raise ValueError("invalid_source_type")
    movie = Movie(
        code=code,
        title=title.strip(),
        description=(description or "").strip(),
        legal_watch_url=(legal_watch_url or "").strip(),
        video_file_id=(video_file_id or "").strip() or None,
        poster_file_id=(poster_file_id or "").strip() or None,
        source_type=(source_type or "").strip(),
        source_note=(source_note or "").strip(),
        year=year,
        genres=(genres or "").strip(),
        language=(language or "uz").strip()[:32],
        subtitle_language=(subtitle_language or "").strip()[:32] or None,
        duration_minutes=duration_minutes,
        status=status if status in MOVIE_STATUSES else "draft",
        created_by_admin_id=admin.id,
        updated_at=datetime.utcnow(),
    )
    session.add(movie)
    await session.commit()
    await session.refresh(movie)
    return movie


async def update_movie_status(session: AsyncSession, movie: Movie, status: str) -> tuple[Movie, list[str]]:
    if status not in MOVIE_STATUSES:
        return movie, ["invalid_status"]
    errors = validate_movie_publishable(movie) if status == "published" else []
    if errors:
        return movie, errors
    movie.status = status
    movie.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(movie)
    return movie, []


async def edit_movie_field(session: AsyncSession, movie: Movie, field: str, value: str) -> tuple[Movie, str | None]:
    field = (field or "").strip().lower()
    value = (value or "").strip()
    allowed = {
        "title", "description", "legal_watch_url", "source_type", "source_note",
        "year", "genres", "language", "subtitle_language", "duration_minutes",
        "video_file_id", "poster_file_id", "original_title",
    }
    if field not in allowed:
        return movie, "invalid_field"
    if field == "source_type" and value not in LEGAL_SOURCE_TYPES:
        return movie, "invalid_source_type"
    if field in {"year", "duration_minutes"}:
        if value in {"", "-", "none", "None"}:
            setattr(movie, field, None)
        else:
            try:
                setattr(movie, field, int(value))
            except ValueError:
                return movie, "invalid_number"
    else:
        setattr(movie, field, value)
    movie.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(movie)
    return movie, None


def movie_admin_summary(movie: Movie) -> str:
    publish_errors = validate_movie_publishable(movie)
    problems = ", ".join(publish_errors) if publish_errors else "none"
    return (
        f"🎬 <b>{movie.title}</b>\n"
        f"Code: <code>{movie.code}</code>\n"
        f"Status: <b>{movie.status}</b>\n"
        f"Year: {movie.year or '-'}\n"
        f"Genres: {movie.genres or '-'}\n"
        f"Language: {movie.language or '-'}\n"
        f"Subtitle: {movie.subtitle_language or '-'}\n"
        f"Duration: {movie.duration_minutes or '-'}\n"
        f"URL/video: {'yes' if (movie.legal_watch_url or movie.video_file_id) else 'no'}\n"
        f"Source: {movie.source_type or '-'}\n"
        f"Source note: {movie.source_note or '-'}\n"
        f"Publish blockers: {problems}\n\n"
        f"Description:\n{movie.description or '-'}"
    )


def _language_flag(language: str | None) -> str:
    code = (language or "").strip().lower()
    flags = {
        "uz": "🇺🇿",
        "ru": "🇷🇺",
        "en": "🇬🇧",
        "tr": "🇹🇷",
        "ko": "🇰🇷",
        "ja": "🇯🇵",
        "zh": "🇨🇳",
        "hi": "🇮🇳",
        "silent": "🔇",
    }
    return flags.get(code, "🌐")


def channel_post_template(movie: Movie, bot_username: str | None = None) -> str:
    code = normalize_movie_code(movie.code)
    deep_link = f"https://t.me/{bot_username}?start=watch_{code}" if bot_username else ""
    movie_type = (getattr(movie, "genres", "") or "Movie").strip() or "Movie"
    title = (getattr(movie, "title", "") or code).strip() or code
    language = (getattr(movie, "language", "") or "uz").strip() or "uz"
    year = getattr(movie, "year", None) or "-"
    parts = [
        f"🎬 {movie_type}: {title}",
        f"Til: {_language_flag(language)} {language}",
        f"Yil: {year}",
        f"Kod: {code}",
        "",
        "Kodni botga yuboring yoki bosib oching:" if deep_link else "Kodni botga yuboring:",
        deep_link if deep_link else code,
        f"👉 @{bot_username}" if bot_username else "",
    ]
    return "\n".join([p for p in parts if p])


async def delete_movie(session: AsyncSession, movie: Movie) -> str:
    code = movie.code
    room_offer_ids = [r[0] for r in (await session.execute(select(RoomMovieOffer.id).where(RoomMovieOffer.movie_id == movie.id))).all()]
    for offer_id in room_offer_ids:
        await session.execute(delete(RoomMovieVote).where(RoomMovieVote.offer_id == offer_id))
    await session.execute(delete(RoomMovieOffer).where(RoomMovieOffer.movie_id == movie.id))
    await session.execute(delete(MovieOffer).where(MovieOffer.movie_id == movie.id))
    await session.delete(movie)
    await session.commit()
    return code


async def release_reserved_anon_name(session: AsyncSession, user: User) -> None:
    await session.execute(delete(ReservedAnonName).where(ReservedAnonName.user_telegram_id == user.telegram_id))


async def reserve_anon_name(session: AsyncSession, user: User) -> str:
    # If this user already has a reserved auto-name, release it first so restart/clean gives a fresh one later.
    await release_reserved_anon_name(session, user)
    for _ in range(20):
        used_names = {r[0] for r in (await session.execute(select(ReservedAnonName.name))).all()}
        available = [name for name in FUNNY_ANON_NAMES if name not in used_names] or [make_anon_name()]
        name = secrets.choice(available)
        session.add(ReservedAnonName(name=name, user_telegram_id=user.telegram_id))
        user.anon_name = name
        try:
            await session.commit()
            await session.refresh(user)
            return name
        except IntegrityError:
            await session.rollback()
            fresh = await get_user_by_id(session, user.id)
            if fresh:
                user = fresh
    # Pool may be exhausted or highly contended; recycle oldest as a final fallback.
    oldest = (await session.execute(select(ReservedAnonName).order_by(ReservedAnonName.id.asc()).limit(1))).scalar_one_or_none()
    if oldest:
        name = oldest.name
        await session.delete(oldest)
        await session.flush()
    else:
        name = make_anon_name()
    session.add(ReservedAnonName(name=name, user_telegram_id=user.telegram_id))
    user.anon_name = name
    await session.commit()
    await session.refresh(user)
    return name


async def create_ad_campaign(session: AsyncSession, admin: User, source_chat_id: int, source_message_id: int) -> AdCampaign:
    # Only one active ad at a time. New ad replaces the previous campaign.
    await session.execute(update(AdCampaign).where(AdCampaign.status == "active").values(status="hidden"))
    ad = AdCampaign(
        source_chat_id=int(source_chat_id),
        source_message_id=int(source_message_id),
        created_by_admin_id=admin.id,
        status="active",
    )
    session.add(ad)
    await session.commit()
    await session.refresh(ad)
    return ad


async def get_active_ad(session: AsyncSession) -> AdCampaign | None:
    result = await session.execute(select(AdCampaign).where(AdCampaign.status == "active").order_by(AdCampaign.id.desc()).limit(1))
    return result.scalar_one_or_none()


async def should_show_ad_now(session: AsyncSession, user: User) -> tuple[bool, AdCampaign | None]:
    if user.is_admin or user.plan == "pro":
        return False, None
    interval = settings.plus_ad_interval if user.plan == "plus" else settings.free_ad_interval
    if interval <= 0:
        return False, None
    user.find_actions_count = (user.find_actions_count or 0) + 1
    await session.commit()
    if user.find_actions_count % interval != 0:
        return False, None
    ad = await get_active_ad(session)
    return bool(ad), ad


async def delete_user_everything(session: AsyncSession, user: User) -> None:
    # Remove memory state first.
    # Release anonymous auto-name reservation so the name returns to the pool.
    await release_reserved_anon_name(session, user)
    WAITING.pop(user.id, None)
    ACTIVE.pop(user.id, None)
    ACTIVE_ROOM.pop(user.id, None)
    await session.execute(delete(WaitingQueue).where(WaitingQueue.user_id == user.id))
    await session.execute(delete(PendingWatchIntent).where(PendingWatchIntent.telegram_id == user.telegram_id))

    # Matches and their offers/messages. Remove both sides from ACTIVE so the
    # other person is never stuck pointing at a deleted match after clean/restart.
    matches = [r[0] for r in (await session.execute(select(Match).where(or_(Match.user_a_id == user.id, Match.user_b_id == user.id)))).all()]
    match_ids = [m.id for m in matches]
    for m in matches:
        ACTIVE.pop(m.user_a_id, None)
        ACTIVE.pop(m.user_b_id, None)
        WAITING.pop(m.user_a_id, None)
        WAITING.pop(m.user_b_id, None)
    for mid in match_ids:
        await session.execute(delete(MovieOffer).where(MovieOffer.match_id == mid))
        await session.execute(delete(ChatMessage).where(ChatMessage.match_id == mid))
    if match_ids:
        await session.execute(delete(Match).where(Match.id.in_(match_ids)))

    # Rooms hosted by user: delete all room-related rows.
    hosted_room_ids = [r[0] for r in (await session.execute(select(Room.id).where(Room.host_user_id == user.id))).all()]
    for rid in hosted_room_ids:
        offer_ids = [r[0] for r in (await session.execute(select(RoomMovieOffer.id).where(RoomMovieOffer.room_id == rid))).all()]
        for oid in offer_ids:
            await session.execute(delete(RoomMovieVote).where(RoomMovieVote.offer_id == oid))
        await session.execute(delete(RoomMovieOffer).where(RoomMovieOffer.room_id == rid))
        await session.execute(delete(RoomMessage).where(RoomMessage.room_id == rid))
        await session.execute(delete(RoomMember).where(RoomMember.room_id == rid))
    if hosted_room_ids:
        await session.execute(delete(Room).where(Room.id.in_(hosted_room_ids)))

    # Rooms where user was only a member.
    await session.execute(delete(RoomMovieVote).where(RoomMovieVote.user_id == user.id))
    user_room_offer_ids = [
        r[0] for r in (await session.execute(
            select(RoomMovieOffer.id).where(RoomMovieOffer.offered_by_user_id == user.id)
        )).all()
    ]
    if user_room_offer_ids:
        await session.execute(delete(RoomMovieVote).where(RoomMovieVote.offer_id.in_(user_room_offer_ids)))
        await session.execute(delete(RoomMovieOffer).where(RoomMovieOffer.id.in_(user_room_offer_ids)))
    await session.execute(delete(RoomMessage).where(RoomMessage.sender_user_id == user.id))
    await session.execute(delete(RoomMember).where(RoomMember.user_id == user.id))

    # Admin-created records must not block account deletion.
    await session.execute(update(Movie).where(Movie.created_by_admin_id == user.id).values(created_by_admin_id=None))
    await session.execute(update(AdCampaign).where(AdCampaign.created_by_admin_id == user.id).values(created_by_admin_id=None))

    await session.execute(update(Payment).where(Payment.user_id == user.id).values(user_id=None))
    await session.execute(delete(UsageDaily).where(UsageDaily.user_id == user.id))
    await session.execute(delete(UserWarning).where(UserWarning.user_id == user.id))
    await session.execute(delete(BanHistory).where(or_(BanHistory.user_id == user.id, BanHistory.admin_user_id == user.id)))
    await session.execute(delete(Report).where(or_(Report.reporter_user_id == user.id, Report.reported_user_id == user.id, Report.reviewed_by_admin_id == user.id)))
    await session.execute(delete(Block).where(or_(Block.blocker_user_id == user.id, Block.blocked_user_id == user.id)))
    await session.delete(user)
    await session.commit()
