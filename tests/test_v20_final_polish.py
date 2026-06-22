from datetime import datetime, timedelta

from app.config import Settings
from app.moderation import check_message
from app.models import User, TelegramRestriction
from app.services import restriction_remaining_text, is_env_admin_id
from app.texts import action_from_text, b, t
from app.utils import FUNNY_ANON_NAMES, valid_anon_name


def test_v20_admin_buttons_and_denial_texts_localized():
    assert action_from_text(b("admin_ads", "uz")) == "admin_ads"
    assert action_from_text(b("admin_ads", "ru")) == "admin_ads"
    assert "kalit" in t("admin_denied", "uz")
    assert "ключ" in t("admin_denied", "ru")
    assert "key" in t("admin_denied", "en")


def test_v20_stronger_contact_detection():
    assert not check_message("mana @abc").allowed
    assert not check_message("telegram @zi_pi123").allowed
    assert not check_message("998901234567").allowed
    assert not check_message("90 123 45 67").allowed
    assert not check_message("example.com").allowed


def test_v20_funny_name_pool_exactly_1000_and_valid():
    assert len(FUNNY_ANON_NAMES) == 1000
    assert len(set(FUNNY_ANON_NAMES)) == 1000
    assert all(valid_anon_name(name) for name in FUNNY_ANON_NAMES)
    assert "SleepySomsa" in FUNNY_ANON_NAMES


def test_v20_restriction_remaining_text():
    r = TelegramRestriction(telegram_id=1, banned_until=datetime.utcnow() + timedelta(minutes=125), reason="3 warnings")
    assert "h" in restriction_remaining_text(r)


def test_v20_ad_settings_defaults():
    s = Settings(bot_token="x")
    assert s.free_ad_interval == 2
    assert s.plus_ad_interval == 5
