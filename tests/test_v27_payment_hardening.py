from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base
from app.models import ActiveMatchParticipant, Payment, UsageDaily, UsageMonthly, User
from app.services import (
    complete_payment,
    consume_movie_unlock,
    create_match,
    get_or_create_user,
    get_active_match,
    model_id,
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


async def _user(session, tid: int, plan: str = "free") -> User:
    user = await get_or_create_user(session, SimpleNamespace(id=tid, username=f"u{tid}", first_name=f"U{tid}", language_code="uz"))
    user.plan = plan
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_v27_complete_payment_is_idempotent_and_extends_once():
    async with temp_session() as session:
        user = await _user(session, 7001)
        payment = Payment(user_id=user.id, plan="plus", duration_months=1, stars_amount=50, invoice_payload="p:v27:once", status="pending")
        session.add(payment)
        await session.commit()
        await session.refresh(payment)

        activated = await complete_payment(session, payment, charge_id="charge-v27", raw_payload="first")
        assert activated is not None
        first_expiry = activated.plan_expires_at
        assert activated.plan == "plus"

        replayed = await complete_payment(session, payment, charge_id="charge-v27", raw_payload="duplicate")
        assert replayed is not None
        assert replayed.plan == "plus"
        assert replayed.plan_expires_at == first_expiry

        saved = (await session.execute(select(Payment).where(Payment.id == payment.id))).scalar_one()
        assert saved.status == "succeeded"
        assert saved.telegram_payment_charge_id == "charge-v27"


@pytest.mark.asyncio
async def test_v27_free_movie_unlock_limit_is_consumed_atomically(monkeypatch):
    import app.services as services

    monkeypatch.setattr(services.settings, "free_daily_movie_unlocks", 1)
    async with temp_session() as session:
        user = await _user(session, 7002)
        ok, used, limit, period = await consume_movie_unlock(session, user)
        assert (ok, used, limit, period) == (True, 0, 1, "daily")
        ok, used, limit, period = await consume_movie_unlock(session, user)
        assert (ok, used, limit, period) == (False, 1, 1, "daily")
        usage = (await session.execute(select(UsageDaily).where(UsageDaily.user_id == model_id(user)))).scalar_one()
        assert usage.movie_unlocks_count == 1


@pytest.mark.asyncio
async def test_v27_plus_movie_unlock_uses_monthly_guard(monkeypatch):
    import app.services as services

    monkeypatch.setattr(services.settings, "plus_monthly_movie_unlocks", 1)
    async with temp_session() as session:
        user = await _user(session, 7003, plan="plus")
        ok, used, limit, period = await consume_movie_unlock(session, user)
        assert (ok, used, limit, period) == (True, 0, 1, "monthly")
        ok, used, limit, period = await consume_movie_unlock(session, user)
        assert (ok, used, limit, period) == (False, 1, 1, "monthly")
        month = date.today().strftime("%Y-%m")
        usage = (await session.execute(select(UsageMonthly).where(UsageMonthly.user_id == model_id(user), UsageMonthly.month == month))).scalar_one()
        assert usage.movie_unlocks_count == 1


@pytest.mark.asyncio
async def test_v27_active_match_participant_guard_tracks_active_users():
    async with temp_session() as session:
        a = await _user(session, 7101)
        b = await _user(session, 7102)
        c = await _user(session, 7103)

        first = await create_match(session, a.id, b.id)
        duplicate = await create_match(session, a.id, c.id)
        assert duplicate.id == first.id

        rows = list((await session.execute(select(ActiveMatchParticipant).where(ActiveMatchParticipant.user_id == model_id(a)))).scalars().all())
        assert len(rows) == 1
        assert (await get_active_match(session, model_id(a))).id == first.id
