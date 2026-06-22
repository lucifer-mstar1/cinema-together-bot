from datetime import datetime, timedelta

import pytest

from app.models import User
from app.services import (
    BOT_BLOCKED_TELEGRAM_IDS,
    WAITING,
    WaitingUser,
    is_bot_blocked,
    mark_bot_blocked,
    mark_bot_unblocked,
    prune_waiting,
)


class DummySession:
    async def execute(self, *args, **kwargs):
        class Result:
            def scalar_one_or_none(self):
                return None
        return Result()

    async def commit(self):
        return None


async def fake_get_user_by_id(session, uid):
    return None


async def fake_is_telegram_restricted(session, telegram_id):
    return False, None


async def fake_get_active_match(session, uid):
    return None


def test_v22_bot_blocked_mark_removes_waiting_and_active_room_state():
    from app.services import ACTIVE, ACTIVE_ROOM

    WAITING.clear()
    ACTIVE.clear()
    ACTIVE_ROOM.clear()
    BOT_BLOCKED_TELEGRAM_IDS.clear()
    WAITING[1] = WaitingUser(user_id=1, telegram_id=111, chat_id=111, lang="uz", mood="casual")
    ACTIVE[1] = 5
    ACTIVE_ROOM[1] = 9

    mark_bot_blocked(111, 1)

    assert is_bot_blocked(111)
    assert 1 not in WAITING
    assert 1 not in ACTIVE
    assert 1 not in ACTIVE_ROOM

    mark_bot_unblocked(111)
    assert not is_bot_blocked(111)


@pytest.mark.asyncio
async def test_v22_prune_waiting_removes_stale_entries(monkeypatch):
    import app.services as services

    WAITING.clear()
    BOT_BLOCKED_TELEGRAM_IDS.clear()
    WAITING[1] = WaitingUser(
        user_id=1,
        telegram_id=111,
        chat_id=111,
        lang="uz",
        mood="casual",
        created_at=datetime.utcnow() - timedelta(minutes=10),
    )
    monkeypatch.setattr(services, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(services, "is_telegram_restricted", fake_is_telegram_restricted)
    monkeypatch.setattr(services, "get_active_match", fake_get_active_match)

    await prune_waiting(DummySession())

    assert WAITING == {}


def test_v22_waiting_user_has_created_at_for_fast_stale_cleanup():
    w = WaitingUser(user_id=1, telegram_id=1, chat_id=1, lang="uz", mood="casual")
    assert isinstance(w.created_at, datetime)
