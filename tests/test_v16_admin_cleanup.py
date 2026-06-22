from types import SimpleNamespace

from app.config import Settings
from app.services import channel_post_template, validate_movie_publishable
from app.texts import b, action_from_text


def test_v16_default_movie_limits():
    settings = Settings(admin_usernames="zi_pi123")
    assert settings.free_daily_movie_unlocks == 3
    assert settings.plus_monthly_movie_unlocks == 150
    assert settings.admin_usernames == ["zi_pi123"]


def test_v16_buttons_are_localized_and_action_parsed():
    assert b("watch_alone", "uz") == "🎬 Yolg‘iz ko‘rish"
    assert b("watch_alone", "ru") == "🎬 Смотреть одному"
    assert b("clean", "en") == "🧹 Clean"
    assert action_from_text("🎬 Смотреть одному") == "watch_alone"
    assert action_from_text("✅ Ha, tozala") == "confirm_clean"


def test_v16_channel_template_has_deep_link_and_bot_mention():
    movie = SimpleNamespace(
        title="The General",
        genres="Classic, Comedy",
        language="silent",
        subtitle_language="uz",
        duration_minutes=75,
        code="TG-1927",
    )
    text = channel_post_template(movie, "cinema_together_test_bot")
    assert "https://t.me/cinema_together_test_bot?start=watch_TG-1927" in text
    assert "@cinema_together_test_bot" in text
    assert "Kodni botga yuboring" in text


def test_v16_publishable_allows_video_file_id_without_url():
    movie = SimpleNamespace(
        title="Owner Test",
        code="OWN-001",
        legal_watch_url="",
        video_file_id="abc123",
        source_type="own_content",
        source_note="Owner uploaded original file.",
    )
    assert validate_movie_publishable(movie) == []
