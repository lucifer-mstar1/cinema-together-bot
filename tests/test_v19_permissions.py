from types import SimpleNamespace

from app.bot import media_allowed_for_user, moderate_text_for_plan
from app.models import User


def user(plan="free", admin=False):
    return User(id=1, telegram_id=1, preferred_language="uz", anon_name="A", plan=plan, is_admin=admin)


def test_free_media_permissions():
    u = user("free")
    assert media_allowed_for_user(u, "text")
    assert media_allowed_for_user(u, "photo")
    assert not media_allowed_for_user(u, "sticker")
    assert not media_allowed_for_user(u, "video")


def test_plus_media_permissions():
    u = user("plus")
    assert media_allowed_for_user(u, "sticker")
    assert media_allowed_for_user(u, "animation")
    assert media_allowed_for_user(u, "audio")
    assert not media_allowed_for_user(u, "video")
    assert not media_allowed_for_user(u, "video_note")


def test_pro_contact_links_blocked_until_mutual_consent_exists():
    u = user("pro")
    assert not moderate_text_for_plan(u, "my telegram @abcde").allowed
    assert not moderate_text_for_plan(u, "https://example.com").allowed


def test_plus_contact_links_blocked():
    u = user("plus")
    assert not moderate_text_for_plan(u, "my telegram @abcde").allowed
    assert not moderate_text_for_plan(u, "https://example.com").allowed
