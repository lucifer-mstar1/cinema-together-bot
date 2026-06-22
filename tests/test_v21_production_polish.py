from app.config import Settings
from app.keyboards import admin_panel_kb
from app.texts import action_from_text, b, t


def test_v21_admin_language_button_all_languages():
    assert action_from_text(b("admin_language", "uz")) == "admin_language"
    assert action_from_text(b("admin_language", "ru")) == "admin_language"
    assert action_from_text(b("admin_language", "en")) == "admin_language"


def test_v21_admin_panel_contains_language_button():
    for lang in ("uz", "ru", "en"):
        kb = admin_panel_kb(lang)
        flat = [button.text for row in kb.keyboard for button in row]
        assert b("admin_language", lang) in flat


def test_v21_clean_settings_defaults_fast_start_style():
    s = Settings(bot_token="x")
    assert s.clean_delete_window >= 100
    assert s.clean_final_message is False


def test_v21_admin_language_texts_localized():
    assert "til" in t("admin_choose_language", "uz").lower()
    assert "язык" in t("admin_choose_language", "ru").lower()
    assert "language" in t("admin_choose_language", "en").lower()
