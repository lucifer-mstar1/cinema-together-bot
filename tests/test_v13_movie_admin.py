import pytest
from types import SimpleNamespace

from app.services import (
    validate_movie_publishable,
    normalize_movie_code,
    channel_post_template,
    generate_movie_code,
)
from app.models import Movie


def test_publish_validation_requires_legal_fields():
    movie = Movie(code="BAD-1", title="Bad", status="draft")
    errors = validate_movie_publishable(movie)
    assert "legal_watch_url_or_video_file_id" in errors
    assert "source_type" in errors
    assert "source_note" in errors


def test_publish_validation_accepts_legal_movie():
    movie = Movie(
        code="OK-1",
        title="OK",
        legal_watch_url="https://example.com/legal",
        source_type="public_domain",
        source_note="Verified public-domain source.",
    )
    assert validate_movie_publishable(movie) == []


def test_normalize_movie_code():
    assert normalize_movie_code(" tg 1927 ") == "TG-1927"


def test_channel_post_template_contains_code_and_bot():
    movie = SimpleNamespace(
        title="The General",
        genres="Classic, Comedy",
        language="silent",
        subtitle_language="uz",
        duration_minutes=75,
        code="TG-1927",
    )
    text = channel_post_template(movie, "cinema_together_test_bot")
    assert "TG-1927" in text
    assert "@cinema_together_test_bot" in text
    assert "Kodni botga yuboring" in text
