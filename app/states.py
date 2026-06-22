from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    rules = State()
    language = State()
    anon_name = State()
    chat_mood = State()


class ChatStates(StatesGroup):
    waiting = State()
    offering_movie = State()
    watch_alone_code = State()
    editing_name = State()
    changing_language = State()
    changing_mood = State()
    clean_confirm = State()

class RoomStates(StatesGroup):
    choosing_type = State()
    entering_title = State()
    joining_by_code = State()
    offering_movie = State()


class AdminMovieStates(StatesGroup):
    code = State()
    title = State()
    movie_type = State()
    language = State()
    year = State()
    video = State()
    delete_number = State()
    post_number = State()


class AdminAdStates(StatesGroup):
    waiting_post = State()
