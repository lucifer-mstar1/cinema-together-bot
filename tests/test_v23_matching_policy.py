import pytest

from app.config import Settings
from app.models import TelegramBlock, User
from app.services import WaitingUser, can_match


def test_v23_rematch_cooldown_default_allows_small_user_base_reuse():
    settings = Settings(bot_token="x")
    assert settings.same_pair_rematch_after_chats == 1


def test_v23_has_telegram_level_block_model_for_clean_restart_safety():
    block = TelegramBlock(blocker_telegram_id=111, blocked_telegram_id=222, reason="manual_block")
    assert block.blocker_telegram_id == 111
    assert block.blocked_telegram_id == 222


@pytest.mark.asyncio
async def test_v23_can_match_uses_pair_cooldown_not_forever_past_match(monkeypatch):
    import app.services as services

    a = User(id=1, telegram_id=101, preferred_language="uz", chat_mood="casual", anon_name="A", trust_score=100)
    b = User(id=2, telegram_id=202, preferred_language="uz", chat_mood="casual", anon_name="B", trust_score=100)
    waiting = WaitingUser(user_id=2, telegram_id=202, chat_id=202, lang="uz", mood="casual")

    async def fake_pair_cooldown(session, a_id, b_id):
        return False

    async def fake_is_blocked(session, a_id, b_id):
        return False

    async def fake_report(session, a_id, b_id):
        return False

    async def fake_get_user_by_id(session, uid):
        return b

    async def fake_restricted(session, telegram_id):
        return False, None

    monkeypatch.setattr(services, "pair_in_rematch_cooldown", fake_pair_cooldown)
    monkeypatch.setattr(services, "is_blocked_between", fake_is_blocked)
    monkeypatch.setattr(services, "has_recent_report_between", fake_report)
    monkeypatch.setattr(services, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(services, "is_telegram_restricted", fake_restricted)
    monkeypatch.setattr(services, "is_recent_pair", lambda *_: False)

    assert await can_match(object(), a, waiting)
