from app.models import Room, RoomMovieOffer, RoomMovieVote
from app.texts import action_from_text, b, t


def test_v10_room_button_actions_exist():
    assert action_from_text(b("create_private_room", "en")) == "create_private_room"
    assert action_from_text(b("join_by_code", "uz")) == "join_by_code"
    assert action_from_text(b("offer_room_movie", "ru")) == "offer_room_movie"
    assert action_from_text(b("host_controls", "en")) == "host_controls"


def test_v10_room_texts_exist():
    assert "invite" in t("room_enter_invite", "en").lower()
    assert "Ovoz" in t("room_vote_registered", "uz")


def test_v10_models_have_room_vote_fields():
    room = Room(host_user_id=1, title="Test", invite_code="ABC123", is_private=True, max_members=7)
    offer = RoomMovieOffer(room_id=1, offered_by_user_id=1, movie_id=1, yes_votes_count=1, status="voting")
    vote = RoomMovieVote(offer_id=1, user_id=1, vote="yes")
    assert room.is_private is True
    assert offer.status == "voting"
    assert vote.vote == "yes"
