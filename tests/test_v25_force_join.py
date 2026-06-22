from types import SimpleNamespace

from app.config import Settings
from app.force_join import _is_member_status, _split_required_chat, is_force_join_exempt_user


def test_v25_force_join_env_parser_accepts_multiple_chat_formats():
    settings = Settings(force_join_chats="@cinema, -100123|https://t.me/+invite|Private Group")
    assert settings.force_join_chats == ["@cinema", "-100123|https://t.me/+invite|Private Group"]

    public_chat = _split_required_chat("@cinema")
    assert public_chat.chat_id == "@cinema"
    assert public_chat.url == "https://t.me/cinema"

    private_chat = _split_required_chat("-100123|https://t.me/+invite|Private Group")
    assert private_chat.chat_id == -100123
    assert private_chat.url == "https://t.me/+invite"
    assert private_chat.title == "Private Group"


def test_v25_force_join_membership_status_rules():
    assert _is_member_status(SimpleNamespace(status="member")) is True
    assert _is_member_status(SimpleNamespace(status="administrator")) is True
    assert _is_member_status(SimpleNamespace(status="left")) is False
    assert _is_member_status(SimpleNamespace(status="kicked")) is False
    assert _is_member_status(SimpleNamespace(status="restricted", is_member=True)) is True
    assert _is_member_status(SimpleNamespace(status="restricted", is_member=False)) is False


def test_v28_force_join_activates_when_any_required_chat_is_entered():
    settings = Settings(force_join_enabled=False, force_join_channels="@main_channel", force_join_groups="-100777|https://t.me/+invite|VIP Group")
    assert settings.force_join_active is True
    assert settings.force_join_items == ["@main_channel", "-100777|https://t.me/+invite|VIP Group"]


def test_v28_force_join_accepts_many_channels_and_groups():
    settings = Settings(
        force_join_chats="@a; @b\n-1001|https://t.me/+one|One Group",
        force_join_channels="https://t.me/public_channel,@second_channel",
        force_join_groups="-1002|https://t.me/+two|Two Group",
    )
    assert settings.force_join_items == [
        "@a",
        "@b",
        "-1001|https://t.me/+one|One Group",
        "https://t.me/public_channel",
        "@second_channel",
        "-1002|https://t.me/+two|Two Group",
    ]


def test_v28_force_join_admin_username_exempt(monkeypatch):
    import app.force_join as force_join

    monkeypatch.setattr(force_join, "settings", Settings(admin_ids=[1], admin_usernames="owner,second_admin"))
    assert is_force_join_exempt_user(SimpleNamespace(id=1, username="someone")) is True
    assert is_force_join_exempt_user(SimpleNamespace(id=2, username="Owner")) is True
    assert is_force_join_exempt_user(SimpleNamespace(id=3, username="normal")) is False
