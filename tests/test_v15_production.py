from app.config import Settings


def test_webhook_url_composes():
    settings = Settings(
        bot_token="x",
        admin_ids="1,2",
        webhook_base_url="https://example.com/",
        webhook_path="/telegram/webhook",
    )
    assert settings.webhook_url == "https://example.com/telegram/webhook"
    assert settings.admin_ids == [1, 2]


def test_bot_mode_validation():
    assert Settings(bot_token="x", bot_mode="polling").bot_mode == "polling"
    assert Settings(bot_token="x", bot_mode="webhook").bot_mode == "webhook"
