from datetime import datetime, timedelta

from app.models import UsageDaily, User
from app.services import can_join_rooms, can_edit_name_after_onboarding, daily_skip_limit, room_limit_for


def make_user(plan="free", admin=False):
    return User(id=1, telegram_id=1, preferred_language="uz", anon_name="A", plan=plan, is_admin=admin)


def test_v11_plan_room_limits():
    assert room_limit_for(make_user("free")) == 0
    assert room_limit_for(make_user("plus")) == 7
    assert room_limit_for(make_user("pro")) == 14


def test_v11_room_join_allows_free_public_taste_by_default():
    assert can_join_rooms(make_user("free"))
    assert can_join_rooms(make_user("plus"))
    assert can_join_rooms(make_user("pro"))


def test_v11_skip_limits_by_plan():
    assert daily_skip_limit(make_user("free")) < daily_skip_limit(make_user("plus")) < daily_skip_limit(make_user("pro"))


def test_v11_name_edit_is_premium_perk():
    assert not can_edit_name_after_onboarding(make_user("free"))
    assert can_edit_name_after_onboarding(make_user("plus"))


def test_v11_usage_daily_model_counts():
    usage = UsageDaily(user_id=1, date="2026-06-17", skips_count=2, movie_unlocks_count=1)
    assert usage.skips_count == 2
    assert usage.movie_unlocks_count == 1
