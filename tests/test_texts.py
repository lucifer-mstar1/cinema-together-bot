from app.texts import action_from_text, b, t


def test_language_texts_exist():
    assert "Suhbatdosh" in b("find", "uz")
    assert "Partner" in b("find", "en")
    assert t("menu", "ru")


def test_action_from_button_text():
    assert action_from_text(b("offer", "uz")) == "offer"
    assert action_from_text(b("next", "en")) == "next"


def test_profile_language_button_actions():
    assert action_from_text(b("language", "uz")) == "language"
    assert action_from_text(b("change_language", "ru")) == "change_language"
    assert action_from_text(b("auto_name", "en")) == "auto_name"
