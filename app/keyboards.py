from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from app.texts import MOOD_BUTTONS, REPORT_REASONS, b, mood_label


def reply(rows: list[list[str]], placeholder: str = "") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=item) for item in row] for row in rows],
        resize_keyboard=True,
        input_field_placeholder=placeholder,
    )


def language_kb() -> ReplyKeyboardMarkup:
    return reply([["O‘zbekcha", "Русский", "English"]], "Language")


def rules_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Rozilik", "ru": "Согласие", "en": "Agreement"}
    return reply([[b("agree", lang)]], placeholders.get(lang, "Agreement"))


def name_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Anonim ism", "ru": "Анонимное имя", "en": "Anonymous name"}
    return reply([[b("auto_name", lang)]], placeholders.get(lang, "Anonymous name"))


def mood_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Suhbat turi", "ru": "Тип разговора", "en": "Chat vibe"}
    return reply(
        [
            [mood_label("casual", lang), mood_label("deep", lang)],
            [mood_label("funny", lang), mood_label("movies", lang)],
            [mood_label("support", lang)],
        ],
        placeholders.get(lang, "Chat vibe"),
    )


def menu_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Asosiy harakat", "ru": "Главное действие", "en": "Main action"}
    return reply(
        [
            [b("find", lang)],
            [b("movies_list", lang), b("rooms", lang)],
            [b("premium", lang), b("profile", lang)],
        ],
        placeholders.get(lang, "Main action"),
    )


def chat_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {
        "uz": "Oddiy xabar yozing...",
        "ru": "Напишите обычное сообщение...",
        "en": "Type a normal message...",
    }
    return reply(
        [
            [b("offer", lang)],
            [b("next", lang), b("end", lang)],
            [b("report", lang), b("block", lang)],
            [b("menu", lang)],
        ],
        placeholders.get(lang, "Type a normal message..."),
    )


def waiting_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Qidiruv...", "ru": "Поиск...", "en": "Searching..."}
    return reply([[b("cancel", lang)]], placeholders.get(lang, "Searching..."))


def cancel_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Bekor qilish", "ru": "Отмена", "en": "Cancel"}
    return reply([[b("cancel", lang)]], placeholders.get(lang, "Cancel"))


def profile_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Profil", "ru": "Профиль", "en": "Profile"}
    return reply(
        [
            [b("edit_name", lang), b("change_mood", lang)],
            [b("change_language", lang), b("usage", lang)],
            [b("rules", lang), b("help", lang)],
            [b("clean", lang)],
            [b("menu", lang)],
        ],
        placeholders.get(lang, "Profile"),
    )


def movie_offer_kb(offer_id: int, lang: str) -> InlineKeyboardMarkup:
    labels = {
        "uz": ("✅ Roziman", "❌ Rad etish", "🔁 Boshqa kino"),
        "ru": ("✅ Согласен", "❌ Отклонить", "🔁 Другой фильм"),
        "en": ("✅ Agree", "❌ Reject", "🔁 Suggest another"),
    }.get(lang, ("✅ Roziman", "❌ Rad etish", "🔁 Boshqa kino"))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=labels[0], callback_data=f"offer:accept:{offer_id}")],
            [
                InlineKeyboardButton(text=labels[1], callback_data=f"offer:reject:{offer_id}"),
                InlineKeyboardButton(text=labels[2], callback_data=f"offer:suggest:{offer_id}"),
            ],
        ]
    )


def report_kb(lang: str) -> InlineKeyboardMarkup:
    rows = []
    for key, translations in REPORT_REASONS.items():
        rows.append([InlineKeyboardButton(text=translations.get(lang, translations["uz"]), callback_data=f"report:{key}:0")])
    block_label = {"uz": "🚫 Shikoyat + bloklash", "ru": "🚫 Жалоба + блок", "en": "🚫 Report + block"}.get(lang, "🚫 Report + block")
    rows.append([InlineKeyboardButton(text=block_label, callback_data="report:other:1")])
    return InlineKeyboardMarkup(inline_keyboard=rows)




def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()

# v10 room polish keyboards override earlier room keyboards.
def room_type_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Xona turi", "ru": "Тип комнаты", "en": "Room type"}
    return reply([[b("create_public_room", lang), b("create_private_room", lang)], [b("cancel", lang)]], placeholders.get(lang, "Room type"))


def room_title_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Xona nomi", "ru": "Название комнаты", "en": "Room title"}
    return reply([[b("auto_title", lang)], [b("cancel", lang)]], placeholders.get(lang, "Room title"))


def rooms_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Xonalar", "ru": "Комнаты", "en": "Rooms"}
    return reply(
        [
            [b("create_room", lang)],
            [b("join_public_room", lang), b("join_by_code", lang)],
            [b("my_room", lang)],
            [b("menu", lang)],
        ],
        placeholders.get(lang, "Rooms"),
    )


def room_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {
        "uz": "Xonaga xabar yozing...",
        "ru": "Напишите сообщение в комнату...",
        "en": "Type a room message...",
    }
    return reply(
        [
            [b("offer_room_movie", lang)],
            [b("members", lang), b("room_info", lang)],
            [b("report_member", lang)],
            [b("host_controls", lang), b("leave_room", lang)],
            [b("menu", lang)],
        ],
        placeholders.get(lang, "Type a room message..."),
    )


def public_room_list_kb(room_rows, lang: str) -> InlineKeyboardMarkup:
    rows = []
    for room, count in room_rows:
        title = str(getattr(room, "title", "Room"))[:32]
        mood = mood_label(getattr(room, "mood", "casual"), lang)
        limit = getattr(room, "max_members", 0)
        rows.append([
            InlineKeyboardButton(
                text=f"👥 {title} · {count}/{limit} · {mood}",
                callback_data=f"roomjoin:{getattr(room, 'id')}",
            )
        ])
    if room_rows:
        labels = {
            "uz": "🎲 Mos public xonaga tasodifiy kirish",
            "ru": "🎲 Войти в подходящую public комнату",
            "en": "🎲 Random matching public room",
        }
        rows.append([InlineKeyboardButton(text=labels.get(lang, labels["en"]), callback_data="roomjoin:random")])
    back = {"uz": "⬅️ Xonalar menyusi", "ru": "⬅️ Меню комнат", "en": "⬅️ Rooms menu"}
    rows.append([InlineKeyboardButton(text=back.get(lang, back["en"]), callback_data="roomjoin:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def room_report_members_kb(members, lang: str) -> InlineKeyboardMarkup:
    rows = []
    for member in members:
        name = getattr(member, "anon_name_snapshot", "member")
        uid = getattr(member, "user_id")
        rows.append([InlineKeyboardButton(text=str(name), callback_data=f"roomreport:{uid}")])
    if not rows:
        rows.append([InlineKeyboardButton(text={"uz":"A’zo yo‘q", "ru":"Нет участников", "en":"No members"}.get(lang, "No members"), callback_data="roomreport:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def room_movie_vote_kb(offer_id: int, lang: str) -> InlineKeyboardMarkup:
    labels = {
        "uz": ("✅ Ha", "❌ Yo‘q"),
        "ru": ("✅ Да", "❌ Нет"),
        "en": ("✅ Yes", "❌ No"),
    }.get(lang, ("✅ Yes", "❌ No"))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=labels[0], callback_data=f"roomoffer:yes:{offer_id}"),
                InlineKeyboardButton(text=labels[1], callback_data=f"roomoffer:no:{offer_id}"),
            ]
        ]
    )


def host_controls_kb(members, lang: str) -> InlineKeyboardMarkup:
    rows = []
    for member in members:
        if getattr(member, "role", "member") == "host":
            continue
        name = getattr(member, "anon_name_snapshot", "member")
        uid = getattr(member, "user_id")
        muted = getattr(member, "is_muted", False)
        mute_label = {"uz": "Mute ochish" if muted else "Mute", "ru": "Снять mute" if muted else "Mute", "en": "Unmute" if muted else "Mute"}.get(lang, "Mute")
        kick_label = {"uz": "Chiqarish", "ru": "Удалить", "en": "Kick"}.get(lang, "Kick")
        rows.append([
            InlineKeyboardButton(text=f"{mute_label}: {name}", callback_data=f"roomctl:mute:{uid}"),
            InlineKeyboardButton(text=f"{kick_label}: {name}", callback_data=f"roomctl:kick:{uid}"),
        ])
    if not rows:
        rows.append([InlineKeyboardButton(text={"uz":"A’zo yo‘q", "ru":"Нет участников", "en":"No members"}.get(lang, "No members"), callback_data="roomctl:none:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def premium_buy_kb(lang: str, mock: bool = False) -> InlineKeyboardMarkup:
    # Final deploy UI: no public test/mock activation buttons. Mock commands remain admin-only.
    labels = {
        "uz": {"plus": "Plus", "pro": "Pro"},
        "ru": {"plus": "Plus", "pro": "Pro"},
        "en": {"plus": "Plus", "pro": "Pro"},
    }.get(lang, {"plus": "Plus", "pro": "Pro"})
    rows = [
        [InlineKeyboardButton(text=f"⭐ {labels['plus']} 1m — 50★", callback_data="buy:plus:1"), InlineKeyboardButton(text=f"⭐ {labels['plus']} 3m — 110★", callback_data="buy:plus:3")],
        [InlineKeyboardButton(text=f"💎 {labels['pro']} 1m — 150★", callback_data="buy:pro:1"), InlineKeyboardButton(text=f"💎 {labels['pro']} 3m — 330★", callback_data="buy:pro:3")],
        [InlineKeyboardButton(text=f"⭐ {labels['plus']} 12m — 550★", callback_data="buy:plus:12"), InlineKeyboardButton(text=f"💎 {labels['pro']} 12m — 1500★", callback_data="buy:pro:12")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def premium_upgrade_kb(lang: str) -> InlineKeyboardMarkup:
    labels = {
        "uz": ("⭐ Plus olish", "💎 Pro olish"),
        "ru": ("⭐ Купить Plus", "💎 Купить Pro"),
        "en": ("⭐ Get Plus", "💎 Get Pro"),
    }.get(lang, ("⭐ Get Plus", "💎 Get Pro"))
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=labels[0], callback_data="buy:plus:1"),
        InlineKeyboardButton(text=labels[1], callback_data="buy:pro:1"),
    ]])

# v13 movie admin keyboards

def admin_movie_code_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    return reply([["AUTO"], [b("cancel", lang)]], "movie code")


def admin_skip_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    return reply([["-"], [b("cancel", lang)]], "- to skip")


# v18 simplified admin panel keyboard
def admin_panel_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Admin panel", "ru": "Админ панель", "en": "Admin panel"}
    return reply(
        [
            [b("admin_create_movie", lang)],
            [b("admin_movies", lang), b("admin_delete_movie", lang)],
            [b("admin_post_template", lang), b("admin_ads", lang)],
            [b("admin_reports", lang), b("admin_stats", lang)],
            [b("admin_language", lang)],
        ],
        placeholders.get(lang, "Admin panel"),
    )

def clean_confirm_kb(lang: str) -> ReplyKeyboardMarkup:
    placeholders = {"uz": "Tasdiqlash", "ru": "Подтверждение", "en": "Confirmation"}
    return reply([[b("confirm_clean", lang)], [b("cancel", lang)]], placeholders.get(lang, "Confirmation"))
