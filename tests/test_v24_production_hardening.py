from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base
from app.models import Match, Payment, ReportStrike, TelegramEntitlement, TelegramRestriction, User
from app.services import (
    WAITING,
    WaitingUser,
    can_match,
    complete_payment,
    create_report,
    delete_user_everything,
    get_or_create_user,
)


@asynccontextmanager
async def temp_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


async def _add_user(session, uid: int, telegram_id: int | None = None, mood: str = "casual") -> User:
    user = User(
        id=uid,
        telegram_id=telegram_id or uid,
        preferred_language="uz",
        anon_name=f"U{uid}",
        chat_mood=mood,
        plan="free",
        trust_score=100,
        warning_count=0,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_v24_mood_mismatch_does_not_match(monkeypatch):
    import app.services as services

    async def no_cooldown(*args, **kwargs):
        return False

    async def no_block(*args, **kwargs):
        return False

    async def no_report(*args, **kwargs):
        return False

    async def no_restriction(*args, **kwargs):
        return False, None

    other_user = User(id=2, telegram_id=202, preferred_language="uz", chat_mood="funny", anon_name="B", trust_score=100)

    async def fake_get_user_by_id(session, uid):
        return other_user

    monkeypatch.setattr(services, "pair_in_rematch_cooldown", no_cooldown)
    monkeypatch.setattr(services, "is_blocked_between", no_block)
    monkeypatch.setattr(services, "has_recent_report_between", no_report)
    monkeypatch.setattr(services, "is_telegram_restricted", no_restriction)
    monkeypatch.setattr(services, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(services, "is_recent_pair", lambda *_: False)

    user = User(id=1, telegram_id=101, preferred_language="uz", chat_mood="deep", anon_name="A", trust_score=100)
    waiting = WaitingUser(user_id=2, telegram_id=202, chat_id=202, lang="uz", mood="funny")

    assert not await can_match(object(), user, waiting)

    waiting.mood = "casual"
    assert await can_match(object(), user, waiting)


@pytest.mark.asyncio
async def test_v24_plan_restores_after_clean_and_payments_remain():
    async with temp_session() as session:
        tg = SimpleNamespace(id=9001, username="paid", first_name="Paid", language_code="uz")
        user = await get_or_create_user(session, tg)
        payment = Payment(
            user_id=user.id,
            plan="plus",
            duration_months=1,
            stars_amount=50,
            invoice_payload="cinema:v24:1:plus:1:test",
            status="pending",
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)

        user = await complete_payment(session, payment, charge_id="stars-test")
        assert user is not None and user.plan == "plus"

        await delete_user_everything(session, user)

        saved_payment = (await session.execute(select(Payment))).scalar_one()
        assert saved_payment.user_id is None
        entitlement = (await session.execute(select(TelegramEntitlement).where(TelegramEntitlement.telegram_id == 9001))).scalar_one()
        assert entitlement.plan == "plus"

        restored = await get_or_create_user(session, tg)
        assert restored.plan == "plus"
        assert restored.plan_expires_at == entitlement.plan_expires_at


@pytest.mark.asyncio
async def test_v24_report_strikes_expire_after_seven_days():
    async with temp_session() as session:
        reported = await _add_user(session, 1, 111)
        reporter_a = await _add_user(session, 2, 222)
        reporter_b = await _add_user(session, 3, 333)
        session.add(ReportStrike(
            reported_telegram_id=reported.telegram_id,
            reporter_telegram_id=999,
            created_at=datetime.utcnow() - timedelta(days=8),
        ))
        session.add(Match(user_a_id=reporter_a.id, user_b_id=reported.id, status="active"))
        session.add(Match(user_a_id=reporter_b.id, user_b_id=reported.id, status="active"))
        await session.commit()

        await create_report(session, reporter_a, "bad_behavior")
        await create_report(session, reporter_b, "bad_behavior")

        restriction = (await session.execute(select(TelegramRestriction).where(TelegramRestriction.telegram_id == reported.telegram_id))).scalar_one_or_none()
        assert restriction is None or restriction.banned_until is None
        await session.refresh(reported)
        assert reported.is_banned is False


@pytest.mark.asyncio
async def test_v24_same_pair_rematch_cooldown_blocks_immediate_reuse():
    async with temp_session() as session:
        a = await _add_user(session, 1, 101)
        b = await _add_user(session, 2, 202)
        session.add(Match(user_a_id=a.id, user_b_id=b.id, status="ended"))
        await session.commit()

        waiting = WaitingUser(user_id=b.id, telegram_id=b.telegram_id, chat_id=b.telegram_id, lang="uz", mood="casual")
        assert not await can_match(session, a, waiting)


@pytest.mark.asyncio
async def test_v24_same_pair_can_rematch_after_one_other_chat_each():
    async with temp_session() as session:
        a = await _add_user(session, 1, 101)
        b = await _add_user(session, 2, 202)
        c = await _add_user(session, 3, 303)
        d = await _add_user(session, 4, 404)
        session.add(Match(user_a_id=a.id, user_b_id=b.id, status="ended"))
        await session.commit()
        session.add(Match(user_a_id=a.id, user_b_id=c.id, status="ended"))
        session.add(Match(user_a_id=b.id, user_b_id=d.id, status="ended"))
        await session.commit()

        waiting = WaitingUser(user_id=b.id, telegram_id=b.telegram_id, chat_id=b.telegram_id, lang="uz", mood="casual")
        assert await can_match(session, a, waiting)


def test_v24_only_one_create_room_flow_definition_exists():
    bot_py = Path("app/bot.py").read_text()
    assert bot_py.count("async def create_room_flow") == 1
