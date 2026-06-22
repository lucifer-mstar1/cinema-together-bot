from app.models import User
from app.services import WaitingUser, is_recent_pair, match_score, remember_recent_pair


def user(uid=1, lang="uz", mood="casual"):
    return User(id=uid, telegram_id=uid, preferred_language=lang, chat_mood=mood, anon_name="A")


def waiting(uid=2, lang="uz", mood="casual"):
    return WaitingUser(user_id=uid, telegram_id=uid, chat_id=uid, lang=lang, mood=mood)


def test_same_mood_scores_higher_than_different_mood():
    u = user(mood="deep")
    assert match_score(u, waiting(mood="deep")) > match_score(u, waiting(mood="funny"))


def test_recent_pair_memory_blocks_immediate_rematch():
    remember_recent_pair(10, 20)
    assert is_recent_pair(10, 20)
    assert is_recent_pair(20, 10)
