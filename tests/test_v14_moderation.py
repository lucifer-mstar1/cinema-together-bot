from datetime import datetime, timedelta

from app.moderation import check_message
from app.models import Report, User
from app.services import format_recent_messages, is_user_muted, muted_remaining_text


def test_v14_blocks_links_and_contacts():
    assert not check_message("visit https://example.com").allowed
    assert check_message("visit https://example.com").category == "link"
    assert not check_message("my telegram is @username123").allowed
    assert check_message("my telegram is @username123").category == "personal_data"


def test_v14_blocks_bad_words_but_allows_normal_chat():
    assert check_message("hello, how was your day?").allowed
    result = check_message("you are an asshole")
    assert not result.allowed
    assert result.category == "bad_word"


def test_v14_muted_remaining_text():
    user = User(id=1, telegram_id=1, preferred_language="en", anon_name="A", muted_until=datetime.utcnow() + timedelta(minutes=90))
    assert is_user_muted(user)
    assert "h" in muted_remaining_text(user)


def test_v14_report_has_review_fields():
    report = Report(reporter_user_id=1, reported_user_id=2, reason="spam", recent_messages="A: spam", status="open")
    assert report.recent_messages == "A: spam"
    assert report.status == "open"
