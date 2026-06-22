from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base
from app.models import Report, User, WaitingQueue
from app.services import (
    has_recent_report_between,
    is_waiting,
    pop_pending_watch_intent,
    save_pending_watch_intent,
    start_waiting,
    waiting_count,
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


async def add_user(session, uid: int, telegram_id: int | None = None, mood: str = "casual") -> User:
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
async def test_v26_pending_watch_intent_is_durable_and_replaces_old_code():
    async with temp_session() as session:
        await save_pending_watch_intent(session, 777, "watch_old code")
        await save_pending_watch_intent(session, 777, "watch_new")

        assert await pop_pending_watch_intent(session, 777) == "NEW"
        assert await pop_pending_watch_intent(session, 777) == ""


@pytest.mark.asyncio
async def test_v26_waiting_queue_is_database_backed_and_consumed_on_match():
    async with temp_session() as session:
        first = await add_user(session, 1, 101)
        second = await add_user(session, 2, 202)

        assert await start_waiting(session, first, chat_id=101, waiting_message_id=10) is None
        assert await is_waiting(session, first.id)
        assert await waiting_count(session) == 1

        partner = await start_waiting(session, second, chat_id=202, waiting_message_id=20)
        assert partner is not None
        assert partner.user_id == first.id
        assert await waiting_count(session) == 0
        rows = (await session.execute(select(WaitingQueue))).scalars().all()
        assert rows == []


@pytest.mark.asyncio
async def test_v26_old_reports_expire_for_matching_but_recent_reports_still_block():
    async with temp_session() as session:
        a = await add_user(session, 1, 101)
        b = await add_user(session, 2, 202)
        session.add(Report(
            reporter_user_id=a.id,
            reported_user_id=b.id,
            reason="old_minor_report",
            created_at=datetime.utcnow() - timedelta(days=30),
        ))
        await session.commit()
        assert not await has_recent_report_between(session, a.id, b.id)

        session.add(Report(
            reporter_user_id=b.id,
            reported_user_id=a.id,
            reason="recent_report",
            created_at=datetime.utcnow(),
        ))
        await session.commit()
        assert await has_recent_report_between(session, a.id, b.id)
