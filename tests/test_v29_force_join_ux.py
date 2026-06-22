from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db import Base
from app.force_join import _split_required_chat, validate_force_join_configuration
from app.services import get_or_create_user


@asynccontextmanager
async def temp_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


def test_v29_force_join_ignores_example_placeholders():
    settings = Settings(
        force_join_chats="@your_channel,-1001234567890|https://t.me/+inviteLink|Private Group",
        force_join_channels="https://t.me/your_channel",
        force_join_groups="",
    )
    assert settings.force_join_items == []
    assert settings.force_join_active is False


def test_v29_private_invite_link_alone_is_rejected():
    assert _split_required_chat("https://t.me/+RealInvite") is None
    settings = Settings(force_join_groups="https://t.me/+RealInvite")
    import app.force_join as fj

    old = fj.settings
    fj.settings = settings
    try:
        errors = validate_force_join_configuration()
    finally:
        fj.settings = old
    assert errors
    assert "-100CHAT_ID" in errors[0]


def test_v29_private_chat_with_id_and_invite_link_is_valid():
    parsed = _split_required_chat("-1001234567890|https://t.me/+RealInvite|VIP Group")
    assert parsed is not None
    assert parsed.chat_id == -1001234567890
    assert parsed.url == "https://t.me/+RealInvite"
    assert parsed.title == "VIP Group"


@pytest.mark.asyncio
async def test_v29_new_user_defaults_to_settings_language(monkeypatch):
    import app.services as services

    monkeypatch.setattr(services, "settings", Settings(default_language="uz", admin_ids=[1]))
    async with temp_session() as session:
        user = await get_or_create_user(session, SimpleNamespace(id=1, username="admin", first_name="Admin", language_code="en"))
        assert user.preferred_language == "uz"
        assert user.is_admin is True
