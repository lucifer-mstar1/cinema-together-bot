from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db import Base
from app.moderation import check_message
from app.models import AdCampaign, Movie, Room, RoomMember, RoomMovieOffer, RoomMovieVote, TelegramEntitlement, User
from app.services import delete_user_everything, get_or_create_user


@asynccontextmanager
async def fk_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_v24_final_clean_nonhost_room_offer_votes_do_not_break_clean():
    async with fk_session() as session:
        user = User(id=1, telegram_id=1, preferred_language="uz", anon_name="A", plan="free")
        host = User(id=2, telegram_id=2, preferred_language="uz", anon_name="H", plan="plus")
        voter = User(id=3, telegram_id=3, preferred_language="uz", anon_name="V", plan="plus")
        session.add_all([user, host, voter])
        await session.flush()
        room = Room(id=1, host_user_id=host.id, title="Room", invite_code="R-ABC123")
        movie = Movie(
            id=1,
            code="M1",
            title="Movie",
            genres="",
            language="uz",
            description="",
            legal_watch_url="",
            source_type="own_content",
            source_note="Admin upload",
            status="published",
        )
        session.add_all([room, movie])
        await session.flush()
        session.add_all([
            RoomMember(room_id=room.id, user_id=user.id, anon_name_snapshot="A"),
            RoomMember(room_id=room.id, user_id=host.id, anon_name_snapshot="H", role="host"),
            RoomMember(room_id=room.id, user_id=voter.id, anon_name_snapshot="V"),
        ])
        await session.flush()
        offer = RoomMovieOffer(room_id=room.id, offered_by_user_id=user.id, movie_id=movie.id)
        session.add(offer)
        await session.flush()
        session.add(RoomMovieVote(offer_id=offer.id, user_id=voter.id, vote="yes"))
        await session.commit()

        await delete_user_everything(session, user)

        assert (await session.execute(select(RoomMovieOffer))).scalars().all() == []
        assert (await session.execute(select(RoomMovieVote))).scalars().all() == []


@pytest.mark.asyncio
async def test_v24_final_clean_admin_ad_reference_does_not_break_clean():
    async with fk_session() as session:
        admin = User(id=1, telegram_id=1, preferred_language="uz", anon_name="Admin", plan="free", is_admin=True)
        session.add(admin)
        await session.flush()
        session.add(AdCampaign(source_chat_id=1, source_message_id=1, created_by_admin_id=admin.id))
        await session.commit()

        await delete_user_everything(session, admin)

        ad = (await session.execute(select(AdCampaign))).scalar_one()
        assert ad.created_by_admin_id is None


def test_v24_final_clean_production_always_disables_mock_payments():
    assert Settings(bot_token="x", app_env="production", mock_payments=True).mock_payments_enabled is False
    assert Settings(bot_token="x", app_env="development", mock_payments=True).mock_payments_enabled is True


def test_v24_final_clean_moderation_blocks_telegram_colon_username():
    assert not check_message("telegram : username").allowed
    assert not check_message("telegram: username123").allowed


@pytest.mark.asyncio
async def test_v24_final_clean_existing_user_restores_active_entitlement():
    async with fk_session() as session:
        tg = SimpleNamespace(id=9009, username="paid", first_name="Paid", language_code="uz")
        user = await get_or_create_user(session, tg)
        session.add(TelegramEntitlement(telegram_id=user.telegram_id, plan="plus", plan_expires_at=None))
        user.plan = "free"
        user.plan_expires_at = None
        await session.commit()

        restored = await get_or_create_user(session, tg)
        assert restored.plan == "plus"


def test_v24_final_clean_no_duplicate_defs_or_dead_admin_password_leftovers():
    keyboard_text = Path("app/keyboards.py").read_text()
    bot_text = Path("app/bot.py").read_text()
    texts_text = Path("app/texts.py").read_text()
    config_text = Path("app/config.py").read_text()

    assert keyboard_text.count("def rooms_kb") == 1
    assert keyboard_text.count("def room_kb") == 1
    assert bot_text.count('@router.message(Command("clean"))') == 1
    assert "admin_password" not in texts_text
    assert "admin_password" not in config_text
