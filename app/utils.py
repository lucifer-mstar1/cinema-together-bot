import random
import html
import re

ADJECTIVES = ["Silent", "Moon", "Blue", "Hidden", "Calm", "Night", "Soft", "Deep", "Lucky", "Bright"]
NOUNS = ["Frame", "Scene", "Echo", "Cloud", "River", "Leaf", "Star", "Shadow", "Dream", "Wave"]

# 1000 funny but safe anonymous names. All are ASCII and fit the name validator.
_FUNNY_PREFIXES = [
    "Sleepy", "Kungfu", "Plov", "Somsa", "Lagmon", "Choy", "Manti", "Qurut", "Shashlik", "Tandir",
    "Disco", "Turbo", "Ninja", "Drama", "Cosmic", "Tiny", "Mega", "Wobbly", "Sneaky", "Happy",
    "Angry", "Confused", "Dizzy", "Flying", "Lazy", "Bossy", "Silent", "Noisy", "Spicy", "Sugar",
    "Pickle", "Potato", "Banana", "Kebab", "Panda", "Penguin", "Camel", "Tiger", "Rabbit", "Octopus"
]
_FUNNY_SUFFIXES = [
    "Ninja", "Somsa", "Plov", "Lagmon", "Choynak", "Qozon", "Kosa", "Palovchi", "Kabobchi", "Manti",
    "Shapka", "Paypoq", "Chappal", "Telefon", "WiFi", "Router", "Robot", "Wizard", "Goblin", "Dragon",
    "Panda", "Penguin", "Camel", "Rabbit", "Octopus", "Tiger", "Koala", "Donut", "Biscuit", "Popcorn",
    "Drama", "Boss", "Pilot", "Captain", "Professor", "Detective", "Ghost", "Shadow", "Moon", "Comet",
    "Rocket", "Bubble", "Cucumber", "Potato", "Banana", "Pickle", "Marmalade", "Qatiq", "Nonvoy", "Beshbarmoq"
]
FUNNY_ANON_NAMES = [f"{prefix}{suffix}" for prefix in _FUNNY_PREFIXES for suffix in _FUNNY_SUFFIXES[:25]]

NAME_RE = re.compile(r"^[A-Za-z0-9_\-]{3,24}$")
CONTACT_RE = re.compile(r"(@[A-Za-z0-9_]{4,}|t\.me/|https?://|\+?\d[\d\s()\-]{7,}\d)", re.IGNORECASE)


def make_anon_name() -> str:
    # Fallback random name. For real onboarding, services.reserve_anon_name()
    # picks a unique unused name from FUNNY_ANON_NAMES.
    return random.choice(FUNNY_ANON_NAMES)


def valid_anon_name(name: str) -> bool:
    return bool(NAME_RE.fullmatch((name or "").strip()))


def has_contact_info(text: str) -> bool:
    return bool(CONTACT_RE.search(text or ""))


def movie_card(movie, lang: str = "uz") -> str:
    labels = {
        "uz": {"code": "Kod", "legal": "Qonuniy manba", "lang": "Til", "genres": "Janr", "duration": "Davomiyligi"},
        "ru": {"code": "Код", "legal": "Легальный источник", "lang": "Язык", "genres": "Жанр", "duration": "Длительность"},
        "en": {"code": "Code", "legal": "Legal source", "lang": "Language", "genres": "Genres", "duration": "Duration"},
    }.get(lang, {"code": "Kod", "legal": "Qonuniy manba", "lang": "Til", "genres": "Janr", "duration": "Davomiyligi"})
    rows = [
        f"<b>{html.escape(movie.title)}</b>",
        f"{labels['code']}: <code>{html.escape(movie.code)}</code>",
    ]
    if getattr(movie, "genres", ""):
        rows.append(f"{labels['genres']}: {html.escape(movie.genres)}")
    if getattr(movie, "language", ""):
        rows.append(f"{labels['lang']}: {html.escape(movie.language)}")
    if getattr(movie, "duration_minutes", None):
        rows.append(f"{labels['duration']}: {movie.duration_minutes} min")
    if movie.description:
        rows.append(html.escape(movie.description))
    if movie.source_note:
        rows.append(f"{labels['legal']}: {html.escape(movie.source_type)} — {html.escape(movie.source_note)}")
    return "\n".join(rows).strip()


def make_invite_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "R-" + "".join(random.choice(alphabet) for _ in range(6))
