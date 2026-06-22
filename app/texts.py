LANGS = {"uz", "ru", "en"}
MOODS = {"casual", "deep", "funny", "movies", "support"}

TEXTS = {
    "welcome": {
        "uz": "🎭 Anonim suhbat botiga xush kelibsiz.\n\nBu yerda asosiy narsa — suhbat. Kino faqat ikkalangiz xohlaganda, keyin taklif qilinadi.\n\nQoidalarga rozimisiz?",
        "ru": "🎭 Добро пожаловать в анонимный чат.\n\nГлавное здесь — общение. Фильм предлагается только позже, если вы оба захотите.\n\nСогласны с правилами?",
        "en": "🎭 Welcome to anonymous chat.\n\nThe core here is conversation. Movies are optional and only come later if both of you want.\n\nDo you agree with the rules?",
    },
    "rules": {
        "uz": "Qoidalar: haqorat, spam, shaxsiy kontakt so‘rash, noqonuniy link va bosim o‘tkazish mumkin emas.",
        "ru": "Правила: нельзя оскорблять, спамить, просить личные контакты, слать нелегальные ссылки или давить на собеседника.",
        "en": "Rules: no harassment, spam, personal contact requests, illegal links, or pressure.",
    },
    "choose_lang": {"uz": "Tilni tanlang:", "ru": "Выберите язык:", "en": "Choose language:"},
    "choose_name": {
        "uz": "Anonim ismingizni yozing. Masalan: SilentMoon\n\nBu haqiqiy username emas, faqat suhbatdagi niqob nom.",
        "ru": "Введите анонимное имя. Например: SilentMoon\n\nЭто не настоящий username, а только имя-маска в чате.",
        "en": "Type your anonymous name. Example: SilentMoon\n\nThis is not your real username, only your chat mask.",
    },
    "choose_mood": {
        "uz": "Bugun qanday suhbat xohlaysiz?",
        "ru": "Какой разговор вы хотите сегодня?",
        "en": "What kind of chat do you want today?",
    },
    "bad_name": {
        "uz": "Ism 3–24 belgi bo‘lsin. Harf, raqam, _ va - ishlatsa bo‘ladi.",
        "ru": "Имя должно быть 3–24 символа. Можно буквы, цифры, _ и -.",
        "en": "Name must be 3–24 chars. Letters, numbers, _ and - are allowed.",
    },
    "profile_done": {"uz": "Profil tayyor. Endi suhbatdosh topishingiz mumkin.", "ru": "Профиль готов. Теперь можно искать собеседника.", "en": "Profile is ready. You can find a chat partner now."},
    "menu": {"uz": "Asosiy menyu:", "ru": "Главное меню:", "en": "Main menu:"},
    "finding": {
        "uz": "🔎 Suhbatdosh qidirilyapti...\nKayfiyat: {mood}\n\nTopilishi bilan shu yerda chat ochiladi.",
        "ru": "🔎 Ищу собеседника...\nНастрой: {mood}\n\nКогда найдётся, чат откроется здесь.",
        "en": "🔎 Finding a partner...\nMood: {mood}\n\nWhen found, the chat will open here.",
    },
    "already_waiting": {"uz": "Siz allaqachon qidiruvdasiz. Kuting yoki bekor qiling.", "ru": "Вы уже в поиске. Подождите или отмените.", "en": "You are already searching. Wait or cancel."},
    "matched": {
        "uz": "✅ Suhbatdosh topildi.\n\nEndi bemalol yozing. Kino haqida gaplashish shart emas — oddiy suhbatdan boshlang.",
        "ru": "✅ Собеседник найден.\n\nТеперь можно свободно писать. Не обязательно говорить о фильмах — начните обычный разговор.",
        "en": "✅ Partner found.\n\nYou can chat freely now. No need to talk about movies — start like a normal anonymous chat.",
    },
    "partner_unavailable": {
        "uz": "Suhbatdosh hozir mavjud emas. Qidiruvni qaytadan bosishingiz mumkin.",
        "ru": "Собеседник сейчас недоступен. Можно начать поиск заново.",
        "en": "That partner is unavailable now. You can start searching again.",
    },
    "chat_help": {"uz": "Suhbat rejimi. Oddiy xabar yozing — men uni anonim yuboraman.", "ru": "Режим чата. Пишите обычное сообщение — я отправлю его анонимно.", "en": "Chat mode. Type normally — I will send it anonymously."},
    "cancelled": {"uz": "Bekor qilindi.", "ru": "Отменено.", "en": "Cancelled."},
    "not_in_chat": {"uz": "Hozir aktiv suhbat yo‘q.", "ru": "Сейчас нет активного чата.", "en": "No active chat right now."},
    "partner_left": {"uz": "Suhbatdosh chiqib ketdi.", "ru": "Собеседник вышел.", "en": "Your partner left."},
    "chat_ended": {"uz": "Suhbat tugatildi.", "ru": "Чат завершён.", "en": "Chat ended."},
    "blocked": {"uz": "Foydalanuvchi bloklandi. U bilan qayta ulanmaymiz.", "ru": "Пользователь заблокирован. Мы больше не соединим вас.", "en": "User blocked. You will not be matched again."},
    "you_were_blocked": {"uz": "Suhbat tugatildi.", "ru": "Чат завершён.", "en": "Chat ended."},
    "banned": {"uz": "Siz botdan vaqtincha cheklangansiz.", "ru": "Вы временно ограничены в боте.", "en": "You are temporarily restricted from the bot."},
    "ask_movie_code": {"uz": "Kino kodini yozing. Masalan: KINO-001\n\nBu kod suhbatdoshga taklif sifatida yuboriladi.", "ru": "Введите код фильма. Например: KINO-001\n\nКод будет отправлен собеседнику как предложение.", "en": "Type the movie code. Example: KINO-001\n\nIt will be sent to your partner as an offer."},
    "movie_not_found": {"uz": "Bu kod topilmadi. Suhbat davom etadi.", "ru": "Код не найден. Чат продолжается.", "en": "Code not found. Chat continues."},
    "offer_sent": {"uz": "Taklif yuborildi. Suhbatni davom ettirishingiz mumkin.", "ru": "Предложение отправлено. Можно продолжать чат.", "en": "Offer sent. You can keep chatting."},
    "offer_received": {"uz": "🎬 Suhbatdoshingiz kino taklif qildi:", "ru": "🎬 Собеседник предложил фильм:", "en": "🎬 Your partner offered a movie:"},
    "offer_accepted": {"uz": "✅ Kino kelishildi. Link yuborildi. Suhbat davom etadi.", "ru": "✅ Фильм согласован. Ссылка отправлена. Чат продолжается.", "en": "✅ Movie agreed. Link sent. Chat continues."},
    "offer_rejected": {"uz": "❌ Kino taklifi rad qilindi. Suhbat davom etadi.", "ru": "❌ Предложение отклонено. Чат продолжается.", "en": "❌ Movie offer rejected. Chat continues."},
    "suggest_another": {"uz": "🔁 Mayli. Avval gaplashib oling yoki boshqa kod taklif qiling.", "ru": "🔁 Хорошо. Сначала обсудите или предложите другой код.", "en": "🔁 Okay. Chat first or offer another code."},
    "contact_warning": {"uz": "⚠️ Xavfsizlik uchun telefon, @username yoki link yubormang. Xabar yuborilmadi.", "ru": "⚠️ Для безопасности не отправляйте телефон, @username или ссылки. Сообщение не отправлено.", "en": "⚠️ For safety, do not share phone, @username, or links. Message was not sent."},
    "report_reason": {"uz": "Shikoyat sababini tanlang:", "ru": "Выберите причину жалобы:", "en": "Choose report reason:"},
    "reported": {"uz": "Shikoyat qabul qilindi.", "ru": "Жалоба принята.", "en": "Report submitted."},
    "reported_blocked": {"uz": "Shikoyat qabul qilindi va foydalanuvchi bloklandi.", "ru": "Жалоба принята, пользователь заблокирован.", "en": "Report submitted and user blocked."},
    "profile_details": {"uz": "👤 Profilingiz\n\nAnonim ism: <b>{name}</b>\nTil: {language}\nSuhbat kayfiyati: {mood}", "ru": "👤 Ваш профиль\n\nАнонимное имя: <b>{name}</b>\nЯзык: {language}\nНастрой чата: {mood}", "en": "👤 Your profile\n\nAnonymous name: <b>{name}</b>\nLanguage: {language}\nChat mood: {mood}"},
    "edit_name": {"uz": "Yangi anonim ismingizni yozing:", "ru": "Введите новое анонимное имя:", "en": "Type your new anonymous name:"},
    "name_updated": {"uz": "Anonim ism yangilandi.", "ru": "Анонимное имя обновлено.", "en": "Anonymous name updated."},
    "language_updated": {"uz": "Til O‘zbekchaga o‘zgartirildi.", "ru": "Язык изменён на русский.", "en": "Language changed to English."},
    "mood_updated": {"uz": "Suhbat kayfiyati yangilandi.", "ru": "Настрой чата обновлён.", "en": "Chat mood updated."},
    "invalid_language": {"uz": "Iltimos, tugmalardan birini tanlang.", "ru": "Пожалуйста, выберите одну из кнопок.", "en": "Please choose one of the buttons."},
    "invalid_mood": {"uz": "Iltimos, kayfiyat tugmalaridan birini tanlang.", "ru": "Пожалуйста, выберите один из вариантов.", "en": "Please choose one of the mood buttons."},
    "already_handled": {"uz": "Bu taklif allaqachon yopilgan.", "ru": "Это предложение уже закрыто.", "en": "This offer is already closed."},
    "not_your_offer": {"uz": "Bu taklif sizning suhbatingizga tegishli emas.", "ru": "Это предложение не относится к вашему чату.", "en": "This offer does not belong to your chat."},
    "missing_data": {"uz": "Ma’lumot topilmadi.", "ru": "Данные не найдены.", "en": "Missing data."},
    'rooms_menu': {'uz': '👥 Xonalar\n\nBu yerda Plus/Pro foydalanuvchilar kichik anonim guruh suhbatlari ochadi.', 'ru': '👥 Комнаты\n\nЗдесь Plus/Pro пользователи создают небольшие анонимные групповые чаты.', 'en': '👥 Rooms\n\nPlus/Pro users can create small anonymous group chats here.'},
    'room_created': {'uz': '✅ Xona ochildi. Endi boshqalar public xonadan qo‘shilishi mumkin.\n\nKod: <b>{code}</b>', 'ru': '✅ Комната создана. Другие могут присоединиться через public комнаты.\n\nКод: <b>{code}</b>', 'en': '✅ Room created. Others can join from public rooms.\n\nCode: <b>{code}</b>'},
    'room_joined': {'uz': '✅ Xonaga kirdingiz. Endi guruhga oddiy xabar yozing.', 'ru': '✅ Вы вошли в комнату. Теперь пишите обычные сообщения в группу.', 'en': '✅ You joined the room. Now type normal messages to the group.'},
    'room_full': {'uz': 'Xona to‘lib qolgan.', 'ru': 'Комната заполнена.', 'en': 'The room is full.'},
    'room_no_public': {'uz': 'Hozircha mos public xona yo‘q. Plus/Pro bo‘lsangiz o‘zingiz xona oching.', 'ru': 'Пока нет подходящей public комнаты. Если у вас Plus/Pro, создайте свою.', 'en': 'No matching public room right now. If you have Plus/Pro, create one.'},
    'room_left': {'uz': 'Xonadan chiqdingiz.', 'ru': 'Вы вышли из комнаты.', 'en': 'You left the room.'},
    'room_partner_left': {'uz': 'Bir foydalanuvchi xonadan chiqdi.', 'ru': 'Пользователь вышел из комнаты.', 'en': 'A user left the room.'},
    'room_members': {'uz': '👥 Xona a’zolari:\n{members}', 'ru': '👥 Участники комнаты:\n{members}', 'en': '👥 Room members:\n{members}'},
    'not_in_room': {'uz': 'Hozir hech qaysi xonada emassiz.', 'ru': 'Вы сейчас не в комнате.', 'en': 'You are not in a room right now.'},
    'already_in_room': {'uz': 'Siz allaqachon xonadasiz. Avval chiqib keting.', 'ru': 'Вы уже в комнате. Сначала выйдите.', 'en': 'You are already in a room. Leave it first.'},
    'finish_chat_first': {'uz': 'Avval hozirgi 1-1 suhbatni tugating.', 'ru': 'Сначала завершите текущий 1-на-1 чат.', 'en': 'End your current 1-to-1 chat first.'},
    'premium_required': {'uz': 'Xona ochish uchun Plus yoki Pro kerak.', 'ru': 'Для создания комнаты нужен Plus или Pro.', 'en': 'Creating rooms requires Plus or Pro.'},
    'grant_ok': {'uz': 'Reja yangilandi: {plan}', 'ru': 'План обновлён: {plan}', 'en': 'Plan updated: {plan}'},
    'room_help': {'uz': 'Xona rejimi. Oddiy xabar yozing — u xonadagi hammaga anonim yuboriladi.', 'ru': 'Режим комнаты. Пишите обычное сообщение — оно анонимно уйдёт всем в комнате.', 'en': 'Room mode. Type normally — it will be sent anonymously to everyone in the room.'},
    "admin": {"uz": "Admin panel", "ru": "Админ панель", "en": "Admin panel"},
}

BUTTONS = {
    "agree": {"uz": "✅ Roziman", "ru": "✅ Согласен", "en": "✅ I agree"},
    "find": {"uz": "🎲 Suhbatdosh topish", "ru": "🎲 Найти партнёра", "en": "🎲 Find Partner"},
    "profile": {"uz": "👤 Profilim", "ru": "👤 Профиль", "en": "👤 Profile"},
    "rules": {"uz": "📜 Qoidalar", "ru": "📜 Правила", "en": "📜 Rules"},
    "help": {"uz": "🆘 Yordam", "ru": "🆘 Помощь", "en": "🆘 Help"},
    "offer": {"uz": "🎬 Kino taklif qilish", "ru": "🎬 Предложить фильм", "en": "🎬 Offer Movie"},
    "next": {"uz": "⏭ Boshqa suhbatdosh", "ru": "⏭ Другой собеседник", "en": "⏭ Next Person"},
    "end": {"uz": "🚪 Suhbatni tugatish", "ru": "🚪 Завершить чат", "en": "🚪 End Chat"},
    "report": {"uz": "⚠️ Shikoyat", "ru": "⚠️ Жалоба", "en": "⚠️ Report"},
    "block": {"uz": "🚫 Bloklash", "ru": "🚫 Заблокировать", "en": "🚫 Block"},
    "menu": {"uz": "⬅️ Menyu", "ru": "⬅️ Меню", "en": "⬅️ Menu"},
    "cancel": {"uz": "❌ Bekor qilish", "ru": "❌ Отмена", "en": "❌ Cancel"},
    "edit_name": {"uz": "✍️ Ismni o‘zgartirish", "ru": "✍️ Изменить имя", "en": "✍️ Edit name"},
    "language": {"uz": "🌐 Til", "ru": "🌐 Язык", "en": "🌐 Language"},
    "change_language": {"uz": "🌐 Tilni o‘zgartirish", "ru": "🌐 Изменить язык", "en": "🌐 Change language"},
    "change_mood": {"uz": "🎭 Suhbat kayfiyati", "ru": "🎭 Настрой чата", "en": "🎭 Chat mood"},
    "auto_name": {"uz": "🎲 Avto ism", "ru": "🎲 Случайное имя", "en": "🎲 Auto name"},
    'rooms': {'uz': '👥 Xonalar', 'ru': '👥 Комнаты', 'en': '👥 Rooms'},
    'create_room': {'uz': '➕ Xona ochish', 'ru': '➕ Создать комнату', 'en': '➕ Create room'},
    'join_public_room': {'uz': '🔎 Public xonaga kirish', 'ru': '🔎 Войти в public комнату', 'en': '🔎 Join public room'},
    'my_room': {'uz': '📋 Xonam', 'ru': '📋 Моя комната', 'en': '📋 My room'},
    'leave_room': {'uz': '🚪 Xonadan chiqish', 'ru': '🚪 Выйти из комнаты', 'en': '🚪 Leave room'},
    'members': {'uz': '👥 A’zolar', 'ru': '👥 Участники', 'en': '👥 Members'},
}

MOOD_BUTTONS = {
    "casual": {"uz": "☕ Oddiy suhbat", "ru": "☕ Обычный разговор", "en": "☕ Casual chat"},
    "deep": {"uz": "🧠 Chuqur suhbat", "ru": "🧠 Глубокий разговор", "en": "🧠 Deep chat"},
    "funny": {"uz": "😄 Kayfiyat ko‘tarish", "ru": "😄 Поднять настроение", "en": "😄 Cheer me up"},
    "movies": {"uz": "🎬 Kino haqida", "ru": "🎬 О фильмах", "en": "🎬 Movie talk"},
    "support": {"uz": "🌙 Shunchaki tinglovchi", "ru": "🌙 Просто слушатель", "en": "🌙 Just someone to listen"},
}

REPORT_REASONS = {
    "harassment": {"uz": "Haqorat", "ru": "Оскорбление", "en": "Harassment"},
    "spam": {"uz": "Spam", "ru": "Спам", "en": "Spam"},
    "personal_data": {"uz": "Shaxsiy ma’lumot", "ru": "Личные данные", "en": "Personal data"},
    "illegal_link": {"uz": "Noqonuniy link", "ru": "Нелегальная ссылка", "en": "Illegal link"},
    "other": {"uz": "Boshqa", "ru": "Другое", "en": "Other"},
}


def norm_lang(lang: str | None) -> str:
    return lang if lang in LANGS else "uz"


def t(key: str, lang: str | None = None) -> str:
    lang = norm_lang(lang)
    return TEXTS[key].get(lang, TEXTS[key]["uz"])


def b(key: str, lang: str | None = None) -> str:
    lang = norm_lang(lang)
    return BUTTONS[key].get(lang, BUTTONS[key]["uz"])


def mood_label(mood: str | None, lang: str | None = None) -> str:
    lang = norm_lang(lang)
    mood = mood if mood in MOODS else "casual"
    return MOOD_BUTTONS[mood].get(lang, MOOD_BUTTONS[mood]["uz"])


def mood_from_text(text: str | None) -> str | None:
    s = (text or "").strip()
    for key, translations in MOOD_BUTTONS.items():
        if s in translations.values():
            return key
    return None


def report_label(reason: str, lang: str | None = None) -> str:
    lang = norm_lang(lang)
    return REPORT_REASONS.get(reason, REPORT_REASONS["other"]).get(lang, REPORT_REASONS["other"]["uz"])


def action_from_text(text: str) -> str | None:
    s = (text or "").strip()
    for key, translations in BUTTONS.items():
        if s in translations.values():
            return key
    return None


def lang_name(lang: str | None, target_lang: str | None = None) -> str:
    lang = norm_lang(lang)
    target_lang = norm_lang(target_lang)
    names = {
        "uz": {"uz": "O‘zbekcha", "ru": "Узбекский", "en": "Uzbek"},
        "ru": {"uz": "Ruscha", "ru": "Русский", "en": "Russian"},
        "en": {"uz": "Inglizcha", "ru": "Английский", "en": "English"},
    }
    return names[lang][target_lang]

# v10 room polish additions
TEXTS.update({
    "room_choose_type": {
        "uz": "Qanday xona ochamiz?\n\nPublic — ro‘yxatdan topiladi.\nPrivate — faqat invite kod bilan kiriladi.",
        "ru": "Какую комнату создать?\n\nPublic — видна в списке.\nPrivate — вход только по invite-коду.",
        "en": "What kind of room?\n\nPublic — discoverable.\nPrivate — invite-code only.",
    },
    "room_enter_title": {
        "uz": "Xona nomini yozing yoki avto nom tanlang.",
        "ru": "Введите название комнаты или выберите авто-название.",
        "en": "Type a room title or choose an automatic title.",
    },
    "room_enter_invite": {
        "uz": "Invite kodni yozing. Masalan: ABC123",
        "ru": "Введите invite-код. Например: ABC123",
        "en": "Type the invite code. Example: ABC123",
    },
    "room_invite_not_found": {
        "uz": "Bunday ochiq xona topilmadi. Kodni tekshiring.",
        "ru": "Открытая комната с таким кодом не найдена. Проверьте код.",
        "en": "No open room found for that code. Check the invite code.",
    },
    "room_info": {
        "uz": "👥 <b>{title}</b>\nTuri: {privacy}\nKod: <code>{code}</code>\nA’zolar: {count}/{limit}\nKayfiyat: {mood}",
        "ru": "👥 <b>{title}</b>\nТип: {privacy}\nКод: <code>{code}</code>\nУчастники: {count}/{limit}\nНастрой: {mood}",
        "en": "👥 <b>{title}</b>\nType: {privacy}\nCode: <code>{code}</code>\nMembers: {count}/{limit}\nMood: {mood}",
    },
    "privacy_public": {"uz": "Public", "ru": "Public", "en": "Public"},
    "privacy_private": {"uz": "Private", "ru": "Private", "en": "Private"},
    "host_only": {
        "uz": "Bu amal faqat xona hosti uchun.",
        "ru": "Это действие доступно только host комнаты.",
        "en": "Only the room host can do this.",
    },
    "room_member_muted": {"uz": "Foydalanuvchi mute qilindi.", "ru": "Пользователь заглушён.", "en": "Member muted."},
    "room_member_unmuted": {"uz": "Mute olib tashlandi.", "ru": "Mute снят.", "en": "Member unmuted."},
    "room_member_kicked": {"uz": "Foydalanuvchi xonadan chiqarildi.", "ru": "Пользователь удалён из комнаты.", "en": "Member removed from room."},
    "you_were_kicked": {"uz": "Siz xonadan chiqarildingiz.", "ru": "Вас удалили из комнаты.", "en": "You were removed from the room."},
    "you_are_muted": {"uz": "Siz bu xonada mute qilingansiz.", "ru": "Вы заглушены в этой комнате.", "en": "You are muted in this room."},
    "room_ask_movie_code": {
        "uz": "Xona uchun kino kodini yozing. Ovoz berish boshlanadi.",
        "ru": "Введите код фильма для комнаты. Начнётся голосование.",
        "en": "Type a movie code for the room. Voting will start.",
    },
    "room_offer_started": {
        "uz": "🎬 Kino ovoz berishga qo‘yildi:",
        "ru": "🎬 Фильм поставлен на голосование:",
        "en": "🎬 Movie vote started:",
    },
    "room_vote_registered": {"uz": "Ovozingiz qabul qilindi.", "ru": "Ваш голос принят.", "en": "Vote registered."},
    "room_vote_result": {
        "uz": "Ovozlar: ✅ {yes} / ❌ {no} / 👥 {total}",
        "ru": "Голоса: ✅ {yes} / ❌ {no} / 👥 {total}",
        "en": "Votes: ✅ {yes} / ❌ {no} / 👥 {total}",
    },
    "room_movie_accepted": {
        "uz": "✅ Xona kino tanladi. Link:\n▶️ {url}",
        "ru": "✅ Комната выбрала фильм. Ссылка:\n▶️ {url}",
        "en": "✅ Room agreed on the movie. Link:\n▶️ {url}",
    },
    "room_movie_rejected": {"uz": "❌ Xona bu kinoni rad etdi.", "ru": "❌ Комната отклонила фильм.", "en": "❌ The room rejected this movie."},
    "room_offer_closed": {"uz": "Bu ovoz berish yopilgan.", "ru": "Это голосование закрыто.", "en": "This vote is already closed."},
})

BUTTONS.update({
    "create_public_room": {"uz": "🌍 Public xona", "ru": "🌍 Public комната", "en": "🌍 Public room"},
    "create_private_room": {"uz": "🔐 Private xona", "ru": "🔐 Private комната", "en": "🔐 Private room"},
    "join_by_code": {"uz": "🔑 Kod bilan kirish", "ru": "🔑 Войти по коду", "en": "🔑 Join by code"},
    "offer_room_movie": {"uz": "🎬 Xonaga kino taklif", "ru": "🎬 Фильм в комнату", "en": "🎬 Offer room movie"},
    "room_info": {"uz": "ℹ️ Xona info", "ru": "ℹ️ Инфо комнаты", "en": "ℹ️ Room info"},
    "host_controls": {"uz": "🛡 Host boshqaruv", "ru": "🛡 Управление host", "en": "🛡 Host controls"},
    "auto_title": {"uz": "🎲 Avto nom", "ru": "🎲 Авто название", "en": "🎲 Auto title"},
})


# v11 premium/limits additions
TEXTS.update({
    "premium_page": {
        "uz": "⭐ <b>Premium</b>\n\nHozirgi reja: <b>{plan}</b>{expires}\n\nFree: 1-1 anonim chat, kuniga {free_skips} skip, kuniga {free_movies} kino unlock. Xonalar yo‘q.\nPlus: xonalar 7 kishigacha, kuniga {plus_skips} skip, oyiga {plus_movies} kino unlock, anonim ismni o‘zgartirish.\nPro: xonalar 14 kishigacha, kuniga {pro_skips} skip, fair-use kino unlock.",
        "ru": "⭐ <b>Premium</b>\n\nТекущий план: <b>{plan}</b>{expires}\n\nFree: 1-на-1 анонимный чат, {free_skips} skip в день, {free_movies} фильм в день. Комнат нет.\nPlus: комнаты до 7 человек, {plus_skips} skip в день, {plus_movies} фильмов в месяц, изменение анонимного имени.\nPro: комнаты до 14 человек, {pro_skips} skip в день, fair-use фильмы.",
        "en": "⭐ <b>Premium</b>\n\nCurrent plan: <b>{plan}</b>{expires}\n\nFree: 1-to-1 anonymous chat, {free_skips} skips/day, {free_movies} movie unlock/day. No rooms.\nPlus: rooms up to 7, {plus_skips} skips/day, {plus_movies} movie unlocks/month, edit anonymous name.\nPro: rooms up to 14, {pro_skips} skips/day, fair-use movies.",
    },
    "premium_expires": {
        "uz": "\nTugash vaqti: {date}",
        "ru": "\nДействует до: {date}",
        "en": "\nExpires: {date}",
    },
    "premium_coming": {
        "uz": "Plus/Pro Telegram Stars orqali mavjud.",
        "ru": "Plus/Pro доступен через Telegram Stars.",
        "en": "Plus/Pro is available through Telegram Stars.",
    },
    "skip_limit": {
        "uz": "Bugungi skip limiti tugadi: {used}/{limit}. Suhbatni tugatishingiz yoki Premium orqali limitni oshirishingiz mumkin.",
        "ru": "Лимит skip на сегодня закончился: {used}/{limit}. Завершите чат или увеличьте лимит через Premium.",
        "en": "Today's skip limit is over: {used}/{limit}. End the chat or upgrade Premium for more.",
    },
    "movie_limit": {
        "uz": "Kino limiti tugadi: {used}/{limit} ({period}). Suhbat davom etadi.",
        "ru": "Лимит фильмов закончился: {used}/{limit} ({period}). Чат продолжается.",
        "en": "Movie limit reached: {used}/{limit} ({period}). Chat continues.",
    },
    "movie_partner_limit": {
        "uz": "Suhbatdoshingizning kino limiti tugagan. Avval gaplashishni davom ettiring yoki boshqa payt sinang.",
        "ru": "У собеседника закончился лимит фильмов. Продолжайте чат или попробуйте позже.",
        "en": "Your partner has no movie unlocks left. Keep chatting or try later.",
    },
    "room_join_premium_required": {
        "uz": "Xonalarga kirish uchun Plus yoki Pro kerak. 1-1 anonim chat Free rejada ishlaydi.",
        "ru": "Для входа в комнаты нужен Plus или Pro. 1-на-1 анонимный чат работает в Free.",
        "en": "Joining rooms requires Plus or Pro. 1-to-1 anonymous chat works on Free.",
    },
    "name_edit_premium_required": {
        "uz": "Anonim ismni keyin o‘zgartirish Plus/Pro imkoniyati. Free rejada onboardingdagi ism qoladi.",
        "ru": "Изменение анонимного имени после регистрации — функция Plus/Pro. В Free остаётся имя из onboarding.",
        "en": "Changing anonymous name later is a Plus/Pro perk. Free keeps the onboarding name.",
    },
    "usage_page": {
        "uz": "📊 Bugungi limitlar\n\nReja: {plan}\nSkip: {skips_used}/{skips_limit}\nKino: {movie_used}/{movie_limit} ({period})",
        "ru": "📊 Лимиты сегодня\n\nПлан: {plan}\nSkip: {skips_used}/{skips_limit}\nФильмы: {movie_used}/{movie_limit} ({period})",
        "en": "📊 Today's limits\n\nPlan: {plan}\nSkips: {skips_used}/{skips_limit}\nMovies: {movie_used}/{movie_limit} ({period})",
    },
})

BUTTONS.update({
    "premium": {"uz": "⭐ Premium", "ru": "⭐ Premium", "en": "⭐ Premium"},
    "usage": {"uz": "📊 Limitlar", "ru": "📊 Лимиты", "en": "📊 Limits"},
})


# v12 Telegram Stars payment additions
TEXTS.update({
    "premium_choose_plan": {
        "uz": "Quyidan Plus yoki Pro tanlang. To‘lov Telegram Stars orqali amalga oshadi.",
        "ru": "Выберите Plus или Pro ниже. Оплата проходит через Telegram Stars.",
        "en": "Choose Plus or Pro below. Payment uses Telegram Stars.",
    },
    "payment_invoice_title": {
        "uz": "CinemaTogether {plan} — {months} oy",
        "ru": "CinemaTogether {plan} — {months} мес.",
        "en": "CinemaTogether {plan} — {months} month(s)",
    },
    "payment_invoice_description": {
        "uz": "{plan} obunasi. Anonim chat qoladi, premium imkoniyatlar ochiladi.",
        "ru": "Подписка {plan}. Анонимный чат остаётся, premium-возможности открываются.",
        "en": "{plan} subscription. Anonymous chat stays core; premium features unlock.",
    },
    "payment_created": {
        "uz": "Invoice yuborildi. Telegram oynasida Stars bilan tasdiqlang.",
        "ru": "Invoice отправлен. Подтвердите оплату Stars в Telegram.",
        "en": "Invoice sent. Confirm with Stars in Telegram.",
    },
    "payment_success": {
        "uz": "✅ To‘lov qabul qilindi. {plan} {months} oyga aktiv bo‘ldi.",
        "ru": "✅ Оплата принята. {plan} активирован на {months} мес.",
        "en": "✅ Payment received. {plan} is active for {months} month(s).",
    },
    "payment_failed": {
        "uz": "To‘lov tekshiruvida xatolik. Qayta urinib ko‘ring yoki /paysupport yozing.",
        "ru": "Ошибка проверки оплаты. Попробуйте снова или напишите /paysupport.",
        "en": "Payment verification failed. Try again or use /paysupport.",
    },
    "mock_payment_done": {
        "uz": "Admin aktivatsiya: {plan} {months} oyga yoqildi.",
        "ru": "Админ-активация: {plan} включён на {months} мес.",
        "en": "Admin activation: {plan} enabled for {months} month(s).",
    },
    "mock_disabled": {
        "uz": "Mock payment productionda o‘chirilgan.",
        "ru": "Mock payment отключён в production.",
        "en": "Mock payment is disabled in production.",
    },
    "paysupport": {
        "uz": "To‘lov bo‘yicha yordam: payment ID, vaqt va muammo tafsilotini admin/supportga yuboring. Admin /reports va loglar orqali tekshiradi.",
        "ru": "Помощь по оплате: отправьте payment ID, время и детали проблемы админу/support. Админ проверит логи.",
        "en": "Payment support: send payment ID, time, and issue details to admin/support. Admin will check logs.",
    },
})

# v14 strong moderation additions
TEXTS.update({
    "message_blocked": {
        "uz": "Xabar yuborilmadi. Sabab: {reason}. Iltimos, anonim chat xavfsizligini saqlang.",
        "ru": "Сообщение не отправлено. Причина: {reason}. Пожалуйста, сохраняйте безопасность анонимного чата.",
        "en": "Message not sent. Reason: {reason}. Please keep anonymous chat safe.",
    },
    "filter_link": {"uz": "linklar ruxsat emas", "ru": "ссылки запрещены", "en": "links are not allowed"},
    "filter_personal_data": {"uz": "shaxsiy kontakt ma’lumoti", "ru": "личные контакты", "en": "personal contact info"},
    "filter_bad_word": {"uz": "haqorat/yomon so‘z", "ru": "оскорбление/грубое слово", "en": "insult/bad word"},
    "filter_too_long": {"uz": "xabar juda uzun", "ru": "сообщение слишком длинное", "en": "message too long"},
    "filter_other": {"uz": "moderatsiya", "ru": "модерация", "en": "moderation"},
    "muted": {
        "uz": "Siz vaqtincha mute qilingansiz. Qolgan vaqt: {time}.",
        "ru": "Вы временно заглушены. Осталось: {time}.",
        "en": "You are temporarily muted. Remaining: {time}.",
    },
    "auto_muted": {
        "uz": "3 ta ogohlantirishdan keyin siz 24 soatga mute qilindingiz. Qolgan vaqt: {time}.",
        "ru": "После 3 предупреждений вы заглушены на 24 часа. Осталось: {time}.",
        "en": "After 3 warnings, you were muted for 24 hours. Remaining: {time}.",
    },
})

# v16 UX/admin cleanup additions
TEXTS.update({
    "watch_alone_intro": {
        "uz": "🎬 Yolg‘iz ko‘rish\n\nKino kodini yozing. Masalan: KINO-001",
        "ru": "🎬 Смотреть одному\n\nВведите код фильма. Например: KINO-001",
        "en": "🎬 Watch alone\n\nType a movie code. Example: KINO-001",
    },
    "watch_alone_sent": {
        "uz": "✅ Kino ochildi. Yolg‘iz ko‘rishingiz yoki keyin suhbatdosh topishingiz mumkin.",
        "ru": "✅ Фильм открыт. Можно смотреть одному или позже найти собеседника.",
        "en": "✅ Movie unlocked. You can watch alone or find a partner later.",
    },
    "movie_video_sent": {
        "uz": "✅ Kino fayli yuborildi. Suhbatdosh topish ham mumkin.",
        "ru": "✅ Файл фильма отправлен. Также можно найти собеседника.",
        "en": "✅ Movie file sent. You can also find a chat partner.",
    },
    "clean_confirm": {
        "uz": "⚠️ Bu amal profilingiz, suhbatlaringiz, blok/reportlar va foydalanish tarixingizni o‘chiradi. Rostdan ham tozalansinmi?",
        "ru": "⚠️ Это удалит профиль, чаты, блоки/жалобы и историю использования. Точно очистить?",
        "en": "⚠️ This deletes your profile, chats, blocks/reports, and usage history. Clean everything?",
    },
    "clean_done": {
        "uz": "✅ Ma’lumotlaringiz o‘chirildi. Qayta boshlash uchun /start bosing.",
        "ru": "✅ Ваши данные удалены. Нажмите /start, чтобы начать заново.",
        "en": "✅ Your data was deleted. Press /start to begin again.",
    },
    "admin_denied": {
        "uz": "Admin kirish rad etildi.",
        "ru": "Доступ администратора запрещён.",
        "en": "Admin access denied.",
    },
    "admin_bad_password": {
        "uz": "Parol noto‘g‘ri. /admin orqali qayta urinib ko‘ring.",
        "ru": "Неверный пароль. Попробуйте снова через /admin.",
        "en": "Wrong password. Try again with /admin.",
    },
    "admin_logged_in": {
        "uz": "✅ Admin panel ochildi.",
        "ru": "✅ Админ панель открыта.",
        "en": "✅ Admin panel opened.",
    },
    "admin_use_login": {
        "uz": "Avval /admin orqali parol bilan kiring.",
        "ru": "Сначала войдите через /admin с паролем.",
        "en": "Use /admin and enter the password first.",
    },
    "admin_logged_out": {
        "uz": "Admin sessiya yopildi.",
        "ru": "Админ сессия закрыта.",
        "en": "Admin session closed.",
    },
    "admin_menu": {
        "uz": "🛠 Admin panel\n\nKerakli amalni tanlang:",
        "ru": "🛠 Админ панель\n\nВыберите действие:",
        "en": "🛠 Admin panel\n\nChoose an action:",
    },
    "admin_stats_text": {
        "uz": "📊 Statistika\n\nUsers: {users}\nMovies: {movies}\nActive chats: {active}\nOpen rooms: {rooms}\nWaiting: {waiting}\nOpen reports: {reports}\nBlocks: {blocks}\nMuted: {muted}\nLow trust: {low_trust}\nPlus active: {plus_active}\nPro active: {pro_active}\nStars today: {stars_today}",
        "ru": "📊 Статистика\n\nUsers: {users}\nMovies: {movies}\nActive chats: {active}\nOpen rooms: {rooms}\nWaiting: {waiting}\nOpen reports: {reports}\nBlocks: {blocks}\nMuted: {muted}\nLow trust: {low_trust}\nPlus active: {plus_active}\nPro active: {pro_active}\nStars today: {stars_today}",
        "en": "📊 Stats\n\nUsers: {users}\nMovies: {movies}\nActive chats: {active}\nOpen rooms: {rooms}\nWaiting: {waiting}\nOpen reports: {reports}\nBlocks: {blocks}\nMuted: {muted}\nLow trust: {low_trust}\nPlus active: {plus_active}\nPro active: {pro_active}\nStars today: {stars_today}",
    },
    "admin_add_movie_start": {
        "uz": "🎬 Kino qo‘shish\n\nKodni yozing yoki AUTO tanlang. Masalan: KINO-001",
        "ru": "🎬 Добавить фильм\n\nВведите код или выберите AUTO. Например: KINO-001",
        "en": "🎬 Add movie\n\nType code or choose AUTO. Example: KINO-001",
    },
    "admin_title": {"uz": "Sarlavha?", "ru": "Название?", "en": "Title?"},
    "admin_year": {"uz": "Yili? O‘tkazish uchun -", "ru": "Год? - чтобы пропустить", "en": "Year? Use - to skip."},
    "admin_genres": {"uz": "Janrlar? Masalan: Comedy, Classic. O‘tkazish uchun -", "ru": "Жанры? Например: Comedy, Classic. - чтобы пропустить", "en": "Genres? Example: Comedy, Classic. Use - to skip."},
    "admin_language": {"uz": "Kino tili? Masalan: uz, ru, en, silent", "ru": "Язык фильма? Например: uz, ru, en, silent", "en": "Movie language? Example: uz, ru, en, silent"},
    "admin_subtitle": {"uz": "Subtitle tili? O‘tkazish uchun -", "ru": "Язык субтитров? - чтобы пропустить", "en": "Subtitle language? Use - to skip."},
    "admin_duration": {"uz": "Davomiyligi daqiqada? O‘tkazish uchun -", "ru": "Длительность в минутах? - чтобы пропустить", "en": "Duration in minutes? Use - to skip."},
    "admin_description": {"uz": "Qisqa ta’rif?", "ru": "Короткое описание?", "en": "Short description?"},
    "admin_watch": {
        "uz": "Legal watch URL yuboring yoki Telegram video/document fayl upload qiling. Bot file_id ni saqlaydi.",
        "ru": "Отправьте legal watch URL или загрузите Telegram video/document. Бот сохранит file_id.",
        "en": "Send a legal watch URL or upload a Telegram video/document. The bot will store the file_id.",
    },
    "admin_source": {"uz": "Manba turini tanlang:", "ru": "Выберите тип источника:", "en": "Choose source type:"},
    "admin_source_note": {"uz": "Nega bu kino qonuniy? Source note yozing:", "ru": "Почему этот фильм легален? Напишите source note:", "en": "Why is this movie legal? Type the source note:"},
    "admin_saved_draft": {
        "uz": "✅ Kino draft sifatida saqlandi. Tekshirib keyin publish qiling:\n\n{summary}\n\nPublish: /admin_publish_movie {code}",
        "ru": "✅ Фильм сохранён как draft. Проверьте и потом publish:\n\n{summary}\n\nPublish: /admin_publish_movie {code}",
        "en": "✅ Movie saved as draft. Review then publish:\n\n{summary}\n\nPublish: /admin_publish_movie {code}",
    },
    "admin_enter_code": {"uz": "Kino kodini yozing:", "ru": "Введите код фильма:", "en": "Type movie code:"},
    "admin_movie_deleted": {"uz": "🗑 Kino o‘chirildi: {code}", "ru": "🗑 Фильм удалён: {code}", "en": "🗑 Movie deleted: {code}"},
    "admin_movie_not_found": {"uz": "Kino topilmadi.", "ru": "Фильм не найден.", "en": "Movie not found."},
    "admin_movie_list_empty": {"uz": "Kino topilmadi.", "ru": "Фильмы не найдены.", "en": "No movies found."},
})

BUTTONS.update({
    "watch_alone": {"uz": "🎬 Yolg‘iz ko‘rish", "ru": "🎬 Смотреть одному", "en": "🎬 Watch alone"},
    "clean": {"uz": "🧹 Tozalash", "ru": "🧹 Очистить", "en": "🧹 Clean"},
    "confirm_clean": {"uz": "✅ Ha, tozala", "ru": "✅ Да, очистить", "en": "✅ Yes, clean"},
    "admin_create_movie": {"uz": "🎬 Kino yaratish", "ru": "🎬 Создать фильм", "en": "🎬 Create movie"},
    "admin_movies": {"uz": "📚 Kinolar", "ru": "📚 Фильмы", "en": "📚 Movies"},
    "admin_delete_movie": {"uz": "🗑 Kino o‘chirish", "ru": "🗑 Удалить фильм", "en": "🗑 Delete movie"},
    "admin_post_template": {"uz": "📣 Kanal posti", "ru": "📣 Пост для канала", "en": "📣 Channel post"},
    "admin_reports": {"uz": "⚠️ Shikoyatlar", "ru": "⚠️ Жалобы", "en": "⚠️ Reports"},
    "admin_stats": {"uz": "📊 Statistika", "ru": "📊 Статистика", "en": "📊 Stats"},
    "admin_generate_code": {"uz": "🔢 Kod yaratish", "ru": "🔢 Создать код", "en": "🔢 Generate code"},
    "admin_logout": {"uz": "🚪 Admin chiqish", "ru": "🚪 Выйти из админки", "en": "🚪 Admin logout"},
})


# v16.2 localization/admin reset fixes
TEXTS.update({
    "welcome_all": {
        "uz": "🎭 CinemaTogether\n\n🇺🇿 Suhbat — asosiy narsa. Kino keyin, faqat siz xohlasangiz.\n🇷🇺 Общение — главное. Фильм потом, только если вы захотите.\n🇬🇧 Conversation is the core. Movies come later only if you want.\n\nTilni tanlang / Выберите язык / Choose language:",
        "ru": "🎭 CinemaTogether\n\n🇺🇿 Suhbat — asosiy narsa. Kino keyin, faqat siz xohlasangiz.\n🇷🇺 Общение — главное. Фильм потом, только если вы захотите.\n🇬🇧 Conversation is the core. Movies come later only if you want.\n\nTilni tanlang / Выберите язык / Choose language:",
        "en": "🎭 CinemaTogether\n\n🇺🇿 Suhbat — asosiy narsa. Kino keyin, faqat siz xohlasangiz.\n🇷🇺 Общение — главное. Фильм потом, только если вы захотите.\n🇬🇧 Conversation is the core. Movies come later only if you want.\n\nTilni tanlang / Выберите язык / Choose language:",
    },
    "rules_after_lang": {
        "uz": "✅ Til tanlandi.\n\nQoidalar: haqorat, spam, shaxsiy kontakt so‘rash, noqonuniy link va bosim o‘tkazish mumkin emas.\n\nRozimisiz?",
        "ru": "✅ Язык выбран.\n\nПравила: нельзя оскорблять, спамить, просить личные контакты, отправлять нелегальные ссылки или давить на собеседника.\n\nСогласны?",
        "en": "✅ Language selected.\n\nRules: no harassment, spam, personal contact requests, illegal links, or pressure.\n\nDo you agree?",
    },
    "clean_done": {
        "uz": "✅ Ma’lumotlaringiz o‘chirildi.\n\nBot endi yangi foydalanuvchidek. Qayta boshlash uchun /start bosing.",
        "ru": "✅ Ваши данные удалены.\n\nТеперь бот как для нового пользователя. Нажмите /start, чтобы начать заново.",
        "en": "✅ Your data was deleted.\n\nThe bot is now like a fresh start. Press /start to begin again.",
    },
    "admin_hint": {
        "uz": "Admin kirish uchun .env ichida ADMIN_USERNAMES sizning Telegram username’ingiz bilan bir xil bo‘lishi kerak. Sizning username: @{username}",
        "ru": "Для входа админа ADMIN_USERNAMES в .env должен совпадать с вашим Telegram username. Ваш username: @{username}",
        "en": "For admin login, ADMIN_USERNAMES in .env must match your Telegram username. Your username: @{username}",
    },
    "admin_movies_title": {"uz": "🎬 <b>Kinolar</b>", "ru": "🎬 <b>Фильмы</b>", "en": "🎬 <b>Movies</b>"},
    "admin_generated_code": {"uz": "Yaratilgan kod: <code>{code}</code>", "ru": "Созданный код: <code>{code}</code>", "en": "Generated code: <code>{code}</code>"},
    "admin_usage_movies": {"uz": "Foydalanish: /admin_movies [draft|published|hidden]", "ru": "Использование: /admin_movies [draft|published|hidden]", "en": "Usage: /admin_movies [draft|published|hidden]"},
    "admin_usage_movie": {"uz": "Foydalanish: /admin_movie CODE", "ru": "Использование: /admin_movie CODE", "en": "Usage: /admin_movie CODE"},
    "admin_usage_publish": {"uz": "Foydalanish: /admin_publish_movie CODE", "ru": "Использование: /admin_publish_movie CODE", "en": "Usage: /admin_publish_movie CODE"},
    "admin_usage_delete": {"uz": "Foydalanish: /admin_delete_movie CODE", "ru": "Использование: /admin_delete_movie CODE", "en": "Usage: /admin_delete_movie CODE"},
    "admin_usage_post": {"uz": "Foydalanish: /admin_post_template CODE", "ru": "Использование: /admin_post_template CODE", "en": "Usage: /admin_post_template CODE"},
    "admin_cannot_publish": {"uz": "Publish qilib bo‘lmaydi. Yetishmayapti: {errors}", "ru": "Нельзя publish. Не хватает: {errors}", "en": "Cannot publish. Missing/invalid: {errors}"},
    "no_open_reports": {"uz": "Ochiq shikoyatlar yo‘q.", "ru": "Открытых жалоб нет.", "en": "No open reports."},
    "invalid": {"uz": "Noto‘g‘ri", "ru": "Неверно", "en": "Invalid"},
})


# v17 admin UX + clean reset + localization hardening
TEXTS.update({
    "admin_menu": {
        "uz": "🛠 <b>Admin panel</b>\n\nSiz hozir admin rejimidasiz. Oddiy foydalanuvchi menyusiga qaytish uchun \"Foydalanuvchi rejimi\" tugmasini bosing.",
        "ru": "🛠 <b>Админ панель</b>\n\nВы сейчас в режиме администратора. Чтобы вернуться в обычный режим, нажмите \"Режим пользователя\".",
        "en": "🛠 <b>Admin panel</b>\n\nYou are in admin mode. Press \"User mode\" to return to the normal user menu.",
    },
    "admin_saved_published": {
        "uz": "✅ Kino saqlandi va publish qilindi. Endi kod orqali ochiladi.\n\n{summary}\n\nKanal uchun post: \"Kanal posti\" tugmasini bosing yoki /admin_post_template {code}",
        "ru": "✅ Фильм сохранён и опубликован. Теперь код работает.\n\n{summary}\n\nПост для канала: нажмите \"Пост для канала\" или /admin_post_template {code}",
        "en": "✅ Movie saved and published. The code works now.\n\n{summary}\n\nChannel post: press \"Channel post\" or use /admin_post_template {code}",
    },
    "admin_movie_list_header": {
        "uz": "🎬 <b>Kinolar ro‘yxati</b>\n\nKodni bosib nusxa oling yoki quyidagi amallardan foydalaning:",
        "ru": "🎬 <b>Список фильмов</b>\n\nНажмите код, чтобы скопировать, или используйте действия ниже:",
        "en": "🎬 <b>Movie list</b>\n\nTap a code to copy it, or use the actions below:",
    },
    "admin_movie_list_footer": {
        "uz": "\nAmallar:\n• Publish: /admin_publish_movie CODE\n• Hide: /admin_hide_movie CODE\n• Kanal posti: /admin_post_template CODE\n• O‘chirish: /admin_delete_movie CODE",
        "ru": "\nДействия:\n• Publish: /admin_publish_movie CODE\n• Hide: /admin_hide_movie CODE\n• Пост: /admin_post_template CODE\n• Удалить: /admin_delete_movie CODE",
        "en": "\nActions:\n• Publish: /admin_publish_movie CODE\n• Hide: /admin_hide_movie CODE\n• Channel post: /admin_post_template CODE\n• Delete: /admin_delete_movie CODE",
    },
    "admin_movie_published": {
        "uz": "✅ Publish qilindi: <code>{code}</code>",
        "ru": "✅ Опубликовано: <code>{code}</code>",
        "en": "✅ Published: <code>{code}</code>",
    },
    "admin_movie_hidden": {
        "uz": "👁‍🗨 Yashirildi: <code>{code}</code>",
        "ru": "👁‍🗨 Скрыто: <code>{code}</code>",
        "en": "👁‍🗨 Hidden: <code>{code}</code>",
    },
    "admin_movie_draft": {
        "uz": "📝 Draftga o‘tkazildi: <code>{code}</code>",
        "ru": "📝 Переведено в draft: <code>{code}</code>",
        "en": "📝 Moved to draft: <code>{code}</code>",
    },
    "admin_edit_usage": {
        "uz": "Foydalanish: /admin_edit_movie CODE field value\nMaydonlar: title, description, legal_watch_url, source_type, source_note, year, genres, language, subtitle_language, duration_minutes, video_file_id, poster_file_id, original_title",
        "ru": "Использование: /admin_edit_movie CODE field value\nПоля: title, description, legal_watch_url, source_type, source_note, year, genres, language, subtitle_language, duration_minutes, video_file_id, poster_file_id, original_title",
        "en": "Usage: /admin_edit_movie CODE field value\nFields: title, description, legal_watch_url, source_type, source_note, year, genres, language, subtitle_language, duration_minutes, video_file_id, poster_file_id, original_title",
    },
    "admin_edit_done": {
        "uz": "✅ Yangilandi: {field} — <code>{code}</code>",
        "ru": "✅ Обновлено: {field} — <code>{code}</code>",
        "en": "✅ Updated: {field} — <code>{code}</code>",
    },
    "admin_edit_failed": {
        "uz": "Tahrirlashda xato: {error}",
        "ru": "Ошибка редактирования: {error}",
        "en": "Edit failed: {error}",
    },
    "admin_back_user": {
        "uz": "Foydalanuvchi menyusiga qaytdingiz. Admin panelga qaytish uchun /admin yozing.",
        "ru": "Вы вернулись в меню пользователя. Чтобы открыть админ панель снова, напишите /admin.",
        "en": "You returned to user menu. Use /admin to open admin panel again.",
    },
    "bot_reset_start": {
        "uz": "🎭 CinemaTogether\n\nBot tozalandi. Qayta boshlash uchun pastdagi Start tugmasini bosing.",
        "ru": "🎭 CinemaTogether\n\nБот очищен. Чтобы начать заново, нажмите кнопку Start ниже.",
        "en": "🎭 CinemaTogether\n\nThe bot was cleaned. Press Start below to begin again.",
    },
    "admin_usage_ban": {
        "uz": "Foydalanish: /ban TELEGRAM_ID sabab",
        "ru": "Использование: /ban TELEGRAM_ID причина",
        "en": "Usage: /ban TELEGRAM_ID reason",
    },
    "admin_usage_unban": {"uz": "Foydalanish: /unban TELEGRAM_ID", "ru": "Использование: /unban TELEGRAM_ID", "en": "Usage: /unban TELEGRAM_ID"},
    "admin_usage_mute": {"uz": "Foydalanish: /mute TELEGRAM_ID SOAT sabab", "ru": "Использование: /mute TELEGRAM_ID ЧАСЫ причина", "en": "Usage: /mute TELEGRAM_ID HOURS reason"},
    "admin_user_not_found": {"uz": "Foydalanuvchi DBda topilmadi.", "ru": "Пользователь не найден в DB.", "en": "User not found in DB."},
    "admin_invalid_id": {"uz": "Telegram ID noto‘g‘ri.", "ru": "Неверный Telegram ID.", "en": "Invalid Telegram ID."},
    "admin_banned_done": {"uz": "Ban qilindi: {id}. Sabab: {reason}", "ru": "Забанен: {id}. Причина: {reason}", "en": "Banned: {id}. Reason: {reason}"},
    "admin_unbanned_done": {"uz": "Bandan chiqarildi: {id}", "ru": "Разбанен: {id}", "en": "Unbanned: {id}"},
    "admin_reports_header": {"uz": "⚠️ <b>Ochiq shikoyatlar</b>", "ru": "⚠️ <b>Открытые жалобы</b>", "en": "⚠️ <b>Open reports</b>"},
    "admin_reports_footer": {"uz": "\nKo‘rish: /report_view ID\nQaror: /review_report ID dismiss|warn|mute24|ban|block", "ru": "\nПросмотр: /report_view ID\nРешение: /review_report ID dismiss|warn|mute24|ban|block", "en": "\nView: /report_view ID\nReview: /review_report ID dismiss|warn|mute24|ban|block"},
})

BUTTONS.update({
    "admin_user_mode": {"uz": "👤 Foydalanuvchi rejimi", "ru": "👤 Режим пользователя", "en": "👤 User mode"},
    "admin_panel": {"uz": "🛠 Admin panel", "ru": "🛠 Админ панель", "en": "🛠 Admin panel"},
})

# v18 simple admin workflow + channel button localization
TEXTS.update({
    "admin_menu": {
        "uz": "🛠 <b>Admin panel</b>\n\nKerakli amalni tanlang. Kino yaratish va o‘chirish endi raqamlar orqali ishlaydi.",
        "ru": "🛠 <b>Админ панель</b>\n\nВыберите действие. Создание и удаление фильмов теперь работают через простой список.",
        "en": "🛠 <b>Admin panel</b>\n\nChoose an action. Movie creation and deletion now use a simple numbered workflow.",
    },
    "admin_denied": {
        "uz": "Bu bo‘lim faqat .env ichidagi ADMIN_IDS ro‘yxatidagi adminlar uchun.",
        "ru": "Этот раздел только для админов из ADMIN_IDS в .env.",
        "en": "This area is only for admins listed in ADMIN_IDS in .env.",
    },
    "admin_add_movie_start": {
        "uz": "🎬 Kino yaratish\n\nKino kodini yozing yoki AUTO tugmasini bosing.\nMasalan: KINO-001",
        "ru": "🎬 Создание фильма\n\nВведите код фильма или нажмите AUTO.\nНапример: KINO-001",
        "en": "🎬 Create movie\n\nType a movie code or press AUTO.\nExample: KINO-001",
    },
    "admin_movie_title_prompt": {
        "uz": "Kino nomini yozing. Masalan: Inception",
        "ru": "Введите название. Например: Inception",
        "en": "Type the movie name. Example: Inception",
    },
    "admin_movie_type_prompt": {
        "uz": "Turini yozing. Masalan: Movie, Cartoon, Anime, Serial",
        "ru": "Введите тип. Например: Movie, Cartoon, Anime, Serial",
        "en": "Type the type. Example: Movie, Cartoon, Anime, Series",
    },
    "admin_movie_language_prompt": {
        "uz": "Til kodini yozing. Masalan: uz, ru, en, tr, silent",
        "ru": "Введите код языка. Например: uz, ru, en, tr, silent",
        "en": "Type language code. Example: uz, ru, en, tr, silent",
    },
    "admin_movie_year_prompt": {
        "uz": "Yilini yozing. Masalan: 2024. Bilmasangiz - yuboring.",
        "ru": "Введите год. Например: 2024. Если неизвестно, отправьте -",
        "en": "Type the year. Example: 2024. Send - if unknown.",
    },
    "admin_movie_invalid_year": {
        "uz": "Yil faqat raqam bo‘lishi kerak. Masalan: 2024 yoki -",
        "ru": "Год должен быть числом. Например: 2024 или -",
        "en": "Year must be a number. Example: 2024 or -",
    },
    "admin_upload_video": {
        "uz": "Endi kinoni <b>video</b> sifatida yuboring.\n\nTelegram video yoki video-document qabul qilinadi. Agar legal tashqi link bo‘lsa, link yuboring.",
        "ru": "Теперь отправьте фильм как <b>видео</b>.\n\nПринимается Telegram video или video-document. Если есть legal external link, отправьте ссылку.",
        "en": "Now send the movie as a <b>video</b>.\n\nTelegram video or video-document is accepted. If it is a legal external link, send the link.",
    },
    "admin_video_only": {
        "uz": "❌ Bu format qabul qilinmaydi. Legal URL, Telegram video yoki video-document yuboring.",
        "ru": "❌ Этот формат не принимается. Отправьте legal URL, Telegram video или video-document.",
        "en": "❌ This format is not accepted. Send a legal URL, Telegram video, or video-document.",
    },
    "admin_duplicate_code": {
        "uz": "Bu kod bazada bor. Boshqa kod yozing yoki AUTO tanlang.",
        "ru": "Этот код уже есть в базе. Введите другой код или выберите AUTO.",
        "en": "This code already exists. Type another code or choose AUTO.",
    },
    "admin_simple_saved": {
        "uz": "✅ Kino saqlandi va publish qilindi.\n\nRaqam: {number}\nKod: <code>{code}</code>\nNomi: <b>{title}</b>\n\nEndi foydalanuvchilar kod orqali yoki kanal deep-link orqali ochishi mumkin.",
        "ru": "✅ Фильм сохранён и опубликован.\n\nНомер: {number}\nКод: <code>{code}</code>\nНазвание: <b>{title}</b>\n\nТеперь пользователи могут открыть его по коду или deep-link из канала.",
        "en": "✅ Movie saved and published.\n\nNumber: {number}\nCode: <code>{code}</code>\nTitle: <b>{title}</b>\n\nUsers can now open it by code or channel deep-link.",
    },
    "admin_movie_list_header": {
        "uz": "🎬 <b>Kinolar ro‘yxati</b>\n\nRaqamlar avtomatik tartiblanadi:",
        "ru": "🎬 <b>Список фильмов</b>\n\nНомера сортируются автоматически:",
        "en": "🎬 <b>Movie list</b>\n\nNumbers are sorted automatically:",
    },
    "admin_movie_list_footer": {
        "uz": "\nO‘chirish uchun \"Kino o‘chirish\" tugmasini bosing va raqamni yozing.",
        "ru": "\nЧтобы удалить, нажмите \"Удалить фильм\" и введите номер.",
        "en": "\nTo delete, press \"Delete movie\" and type the number.",
    },
    "admin_delete_choose_number": {
        "uz": "🗑 Qaysi kinoni o‘chiramiz?\n\n{movies}\n\nKino raqamini yozing. Masalan: 1",
        "ru": "🗑 Какой фильм удалить?\n\n{movies}\n\nВведите номер фильма. Например: 1",
        "en": "🗑 Which movie should be deleted?\n\n{movies}\n\nType the movie number. Example: 1",
    },
    "admin_post_choose_number": {
        "uz": "📣 Qaysi kino uchun kanal posti kerak?\n\n{movies}\n\nKino raqamini yozing. Masalan: 1",
        "ru": "📣 Для какого фильма нужен пост канала?\n\n{movies}\n\nВведите номер фильма. Например: 1",
        "en": "📣 Which movie needs a channel post?\n\n{movies}\n\nType the movie number. Example: 1",
    },
    "admin_invalid_movie_number": {
        "uz": "Noto‘g‘ri raqam. Ro‘yxatdan mavjud raqamni tanlang.",
        "ru": "Неверный номер. Выберите номер из списка.",
        "en": "Invalid number. Choose a number from the list.",
    },
    "admin_movie_deleted": {
        "uz": "🗑 O‘chirildi: <code>{code}</code>\n\nRo‘yxat avtomatik qayta tartiblandi.",
        "ru": "🗑 Удалено: <code>{code}</code>\n\nСписок автоматически пересортирован.",
        "en": "🗑 Deleted: <code>{code}</code>\n\nThe list was automatically renumbered.",
    },
    "movies_channel_text": {
        "uz": "🎬 Kinolar ro‘yxati kanalimizda. Ochish uchun tugmani bosing.",
        "ru": "🎬 Список фильмов в нашем канале. Нажмите кнопку, чтобы открыть.",
        "en": "🎬 Movie list is in our channel. Press the button to open it.",
    },
    "movies_channel_missing": {
        "uz": "Kanal hali sozlanmagan. .env ichida MOVIES_CHANNEL_URL yoki MOVIES_CHANNEL_USERNAME kiriting.",
        "ru": "Канал ещё не настроен. Укажите MOVIES_CHANNEL_URL или MOVIES_CHANNEL_USERNAME в .env.",
        "en": "Channel is not configured yet. Set MOVIES_CHANNEL_URL or MOVIES_CHANNEL_USERNAME in .env.",
    },
    "open_movies_channel": {
        "uz": "📺 Kanalni ochish",
        "ru": "📺 Открыть канал",
        "en": "📺 Open channel",
    },
})

BUTTONS.update({
    "movies_list": {"uz": "🎬 Kino kodlari", "ru": "🎬 Коды фильмов", "en": "🎬 Movie Codes"},
    "admin_create_movie": {"uz": "🎬 Kino qo‘shish", "ru": "🎬 Добавить фильм", "en": "🎬 Add movie"},
    "admin_movies": {"uz": "📚 Kinolar", "ru": "📚 Фильмы", "en": "📚 Movies"},
    "admin_delete_movie": {"uz": "🗑 Kino o‘chirish", "ru": "🗑 Удалить фильм", "en": "🗑 Delete movie"},
    "admin_post_template": {"uz": "📣 Kanal posti", "ru": "📣 Пост для канала", "en": "📣 Channel post"},
    "admin_reports": {"uz": "⚠️ Shikoyatlar", "ru": "⚠️ Жалобы", "en": "⚠️ Reports"},
    "admin_stats": {"uz": "📊 Statistika", "ru": "📊 Статистика", "en": "📊 Stats"},
})


# v19 payment clarity + plan media permissions
TEXTS.update({
    "premium_payment_note": {
        "uz": "💳 To‘lov Telegram Stars orqali avtomatik ishlaydi. To‘lov muvaffaqiyatli bo‘lsa, Plus/Pro darhol ochiladi. Stars bot balansiga tushadi; yechib olish Telegram/Fragment orqali bot egasi tomonidan qilinadi.",
        "ru": "💳 Оплата работает автоматически через Telegram Stars. После успешной оплаты Plus/Pro включается сразу. Stars попадают на баланс бота; вывод делает владелец бота через Telegram/Fragment.",
        "en": "💳 Payment works automatically through Telegram Stars. After successful payment, Plus/Pro activates immediately. Stars go to the bot balance; withdrawal is handled by the bot owner via Telegram/Fragment.",
    },
    "media_not_allowed": {
        "uz": "Bu turdagi fayl sizning rejangizda ruxsat emas. Hozirgi reja: {plan}\n\nFree: matn/emoji + rasm.\nPlus: rasm, sticker, GIF, audio. Video faqat Pro.",
        "ru": "Этот тип файла недоступен на вашем плане. Текущий план: {plan}\n\nFree: текст/эмодзи + фото.\nPlus: фото, стикер, GIF, аудио. Видео только Pro.",
        "en": "This media type is not allowed on your plan. Current plan: {plan}\n\nFree: text/emoji + photos.\nPlus: photos, stickers, GIFs, audio. Video is Pro only.",
    },
    "media_only_in_chat": {
        "uz": "Media yuborish uchun avval suhbat yoki xonaga kiring.",
        "ru": "Чтобы отправлять медиа, сначала войдите в чат или комнату.",
        "en": "Join a chat or room before sending media.",
    },
    "media_copy_failed": {
        "uz": "Media yuborishda xatolik bo‘ldi.",
        "ru": "Не удалось отправить медиа.",
        "en": "Could not deliver the media.",
    },
    "media_text": {"uz": "xabar", "ru": "сообщение", "en": "message"},
    "media_photo": {"uz": "rasm yubordi", "ru": "отправил(а) фото", "en": "sent a photo"},
    "media_sticker": {"uz": "sticker yubordi", "ru": "отправил(а) стикер", "en": "sent a sticker"},
    "media_animation": {"uz": "GIF yubordi", "ru": "отправил(а) GIF", "en": "sent a GIF"},
    "media_audio": {"uz": "audio yubordi", "ru": "отправил(а) аудио", "en": "sent audio"},
    "media_voice": {"uz": "ovozli xabar yubordi", "ru": "отправил(а) голосовое", "en": "sent a voice message"},
    "media_video": {"uz": "video yubordi", "ru": "отправил(а) видео", "en": "sent a video"},
    "media_video_note": {"uz": "circle video yubordi", "ru": "отправил(а) кружок", "en": "sent a circle video"},
    "media_document": {"uz": "fayl yubordi", "ru": "отправил(а) файл", "en": "sent a file"},
    "media_other": {"uz": "media yubordi", "ru": "отправил(а) медиа", "en": "sent media"},
})

# v20 final polish: auto-admin, funny denial, ads, localized bans.
TEXTS.update({
    "admin_menu": {
        "uz": "🛠 <b>Admin panel</b>\n\nKerakli amalni tanlang. Bu panel faqat adminlar uchun — oddiy foydalanuvchi menyusi adminlarga ko‘rinmaydi.",
        "ru": "🛠 <b>Админ панель</b>\n\nВыберите действие. Эта панель только для админов — обычное меню пользователям-админам не показывается.",
        "en": "🛠 <b>Admin panel</b>\n\nChoose an action. This panel is admin-only — the normal user menu is hidden for admins.",
    },
    "admin_denied": {
        "uz": "😄 Voy-voy, siz admin eshigini taqillatdingiz, lekin kalit sizda emas ekan. Boshqa safar omad!",
        "ru": "😄 Ого, вы постучали в админ-дверь, но ключика нет. Попробуйте удачу в другой раз!",
        "en": "😄 Wow, you knocked on the admin door, but the key is not yours. Try your luck another time!",
    },
    "admin_auto_only": {
        "uz": "Siz adminsiz. Quyidagi admin paneldan foydalaning:",
        "ru": "Вы админ. Используйте панель ниже:",
        "en": "You are an admin. Use the panel below:",
    },
    "admin_ad_start": {
        "uz": "📢 Reklama yaratish\n\nFoydalanuvchilarga ko‘rinishi kerak bo‘lgan postni yuboring: matn, rasm+caption yoki video+caption. Yuborgan xabaringiz aynan reklama sifatida saqlanadi.",
        "ru": "📢 Создание рекламы\n\nОтправьте пост, который увидят пользователи: текст, фото+caption или видео+caption. Это сообщение будет сохранено как реклама.",
        "en": "📢 Create ad\n\nSend the post users should see: text, photo+caption, or video+caption. That exact message will be saved as the ad.",
    },
    "admin_ad_saved": {
        "uz": "✅ Reklama saqlandi.\n\nFree foydalanuvchi har {free} ta suhbat qidirishda bir marta ko‘radi. Plus har {plus} marta. Pro hech qachon reklama ko‘rmaydi.",
        "ru": "✅ Реклама сохранена.\n\nFree увидит её раз в {free} поисков собеседника. Plus — раз в {plus}. Pro рекламу не видит.",
        "en": "✅ Ad saved.\n\nFree users see it once every {free} partner searches. Plus sees it once every {plus}. Pro never sees ads.",
    },
    "admin_ad_failed": {
        "uz": "Reklamani saqlab bo‘lmadi. Yana bir marta yuboring.",
        "ru": "Не удалось сохранить рекламу. Отправьте ещё раз.",
        "en": "Could not save the ad. Send it one more time.",
    },
    "auto_banned_2h": {
        "uz": "⛔ 3 ta ogohlantirishdan keyin 2 soatga cheklov qo‘yildi. Qolgan vaqt: {time}.",
        "ru": "⛔ После 3 предупреждений ограничение на 2 часа. Осталось: {time}.",
        "en": "⛔ After 3 warnings, you are restricted for 2 hours. Remaining: {time}.",
    },
    "banned_until": {
        "uz": "⛔ Siz vaqtincha cheklangansiz. Qolgan vaqt: {time}.",
        "ru": "⛔ Вы временно ограничены. Осталось: {time}.",
        "en": "⛔ You are temporarily restricted. Remaining: {time}.",
    },
    "report_auto_ban_notice": {
        "uz": "⛔ 3 ta shikoyatdan keyin foydalanuvchi 2 soatga cheklangan.",
        "ru": "⛔ После 3 жалоб пользователь ограничен на 2 часа.",
        "en": "⛔ After 3 reports, the user was restricted for 2 hours.",
    },
})

BUTTONS.update({
    "admin_ads": {"uz": "📢 Reklama", "ru": "📢 Реклама", "en": "📢 Ads"},
})


# v24 keeps previous admin language + clean labels + localized admin command fallbacks.
TEXTS.update({
    "admin_menu": {
        "uz": "🛠 <b>Admin panel</b>\n\nKerakli amalni tanlang. Tilni pastdagi 🌐 tugma orqali o‘zgartirasiz.",
        "ru": "🛠 <b>Админ панель</b>\n\nВыберите действие. Язык можно изменить кнопкой 🌐 ниже.",
        "en": "🛠 <b>Admin panel</b>\n\nChoose an action. Change language with the 🌐 button below.",
    },
    "admin_language_changed": {
        "uz": "✅ Admin panel tili O‘zbekchaga o‘zgardi.",
        "ru": "✅ Язык админ-панели изменён на русский.",
        "en": "✅ Admin panel language changed to English.",
    },
    "admin_choose_language": {
        "uz": "Admin panel tilini tanlang:",
        "ru": "Выберите язык админ-панели:",
        "en": "Choose admin panel language:",
    },
    "clean_fast_started": {
        "uz": "🧹 Tozalanmoqda...",
        "ru": "🧹 Очистка...",
        "en": "🧹 Cleaning...",
    },
    "clean_fallback": {
        "uz": "🎭 CinemaTogether\n\nQayta boshlash uchun START bosing.",
        "ru": "🎭 CinemaTogether\n\nНажмите START, чтобы начать заново.",
        "en": "🎭 CinemaTogether\n\nPress START to begin again.",
    },
    "admin_usage_post": {
        "uz": "Kanal posti uchun avval kinoni tanlang yoki /admin_post_template KOD yozing.",
        "ru": "Для поста канала выберите фильм или напишите /admin_post_template КОД.",
        "en": "For a channel post, choose a movie or type /admin_post_template CODE.",
    },
    "admin_post_not_found": {
        "uz": "Kino topilmadi. Kinolar ro‘yxatidan raqam tanlang.",
        "ru": "Фильм не найден. Выберите номер из списка фильмов.",
        "en": "Movie not found. Choose a number from the movie list.",
    },
    "admin_report_usage": {
        "uz": "Shikoyatni ko‘rish: /report_view ID",
        "ru": "Просмотр жалобы: /report_view ID",
        "en": "View report: /report_view ID",
    },
    "admin_report_not_found": {
        "uz": "Shikoyat topilmadi.",
        "ru": "Жалоба не найдена.",
        "en": "Report not found.",
    },
    "admin_review_usage": {
        "uz": "Qaror: /review_report ID dismiss|warn|mute24|ban|block",
        "ru": "Решение: /review_report ID dismiss|warn|mute24|ban|block",
        "en": "Review: /review_report ID dismiss|warn|mute24|ban|block",
    },
    "admin_invalid_id": {
        "uz": "Telegram ID noto‘g‘ri.",
        "ru": "Неверный Telegram ID.",
        "en": "Invalid Telegram ID.",
    },
    "admin_usage_ban": {
        "uz": "Foydalanish: /ban TELEGRAM_ID sabab",
        "ru": "Использование: /ban TELEGRAM_ID причина",
        "en": "Usage: /ban TELEGRAM_ID reason",
    },
    "admin_usage_unban": {
        "uz": "Foydalanish: /unban TELEGRAM_ID",
        "ru": "Использование: /unban TELEGRAM_ID",
        "en": "Usage: /unban TELEGRAM_ID",
    },
    "admin_usage_mute": {
        "uz": "Foydalanish: /mute TELEGRAM_ID SOAT sabab",
        "ru": "Использование: /mute TELEGRAM_ID ЧАСЫ причина",
        "en": "Usage: /mute TELEGRAM_ID HOURS reason",
    },
    "admin_usage_grant": {
        "uz": "Foydalanish: /grant TELEGRAM_ID plus|pro|free [kun]",
        "ru": "Использование: /grant TELEGRAM_ID plus|pro|free [дни]",
        "en": "Usage: /grant TELEGRAM_ID plus|pro|free [days]",
    },
    "admin_usage_mock_pay": {
        "uz": "Foydalanish: /mock_pay TELEGRAM_ID plus|pro OY",
        "ru": "Использование: /mock_pay TELEGRAM_ID plus|pro МЕСЯЦЫ",
        "en": "Usage: /mock_pay TELEGRAM_ID plus|pro MONTHS",
    },
    "admin_user_not_found": {
        "uz": "Foydalanuvchi hali DBda yo‘q.",
        "ru": "Пользователя ещё нет в DB.",
        "en": "User is not in the DB yet.",
    },
    "admin_invalid_plan": {
        "uz": "Reja free, plus yoki pro bo‘lishi kerak.",
        "ru": "План должен быть free, plus или pro.",
        "en": "Plan must be free, plus, or pro.",
    },
    "admin_invalid_payment_args": {
        "uz": "Telegram ID yoki muddat noto‘g‘ri.",
        "ru": "Неверный Telegram ID или срок.",
        "en": "Invalid Telegram ID or duration.",
    },
    "invalid_action": {
        "uz": "Amal noto‘g‘ri.",
        "ru": "Неверное действие.",
        "en": "Invalid action.",
    },
})


TEXTS.update({
    "waiting_timeout": {
        "uz": "🕐 Hozir mos suhbatdosh topilmadi. Qayta urinib ko‘ring yoki xonalarga kiring — kechki aktiv vaqtlarda tezroq topiladi.",
        "ru": "🕐 Сейчас подходящий собеседник не найден. Попробуйте ещё раз или зайдите в комнаты — вечером обычно быстрее.",
        "en": "🕐 No matching partner right now. Try again or join rooms — evening active hours usually match faster.",
    },
    "room_report_choose": {
        "uz": "Kimdan shikoyat qilmoqchisiz?",
        "ru": "На кого хотите пожаловаться?",
        "en": "Which member do you want to report?",
    },
    "room_reported": {
        "uz": "Xona a’zosi bo‘yicha shikoyat qabul qilindi.",
        "ru": "Жалоба на участника комнаты принята.",
        "en": "Room member report submitted.",
    },
})

BUTTONS.update({
    "report_member": {"uz": "⚠️ A’zodan shikoyat", "ru": "⚠️ Пожаловаться", "en": "⚠️ Report member"},
})
BUTTONS.update({
    "admin_language": {"uz": "🌐 Admin tili", "ru": "🌐 Язык админки", "en": "🌐 Admin language"},
})



TEXTS.update({
    "force_join_required": {
        "uz": "🔒 Botdan foydalanish uchun quyida qolgan kanal/guruhlarga qo‘shiling. Qo‘shilganlari ro‘yxatdan avtomatik o‘chadi. Keyin «Tekshirish» tugmasini bosing.",
        "ru": "🔒 Чтобы пользоваться ботом, вступите в оставшиеся каналы/группы ниже. Уже пройденные автоматически исчезнут из списка. Затем нажмите «Проверить».",
        "en": "🔒 To use the bot, join the remaining channels/groups below. Already joined ones disappear from this list automatically. Then press “Check”.",
    },
    "force_join_open": {
        "uz": "Qo‘shilish",
        "ru": "Вступить",
        "en": "Join",
    },
    "force_join_check": {
        "uz": "✅ Tekshirish",
        "ru": "✅ Проверить",
        "en": "✅ Check",
    },
    "force_join_not_ready": {
        "uz": "Hali hamma kanal/guruhlarga qo‘shilmagansiz.",
        "ru": "Вы ещё не вступили во все нужные каналы/группы.",
        "en": "You still have not joined every required channel/group.",
    },
    "force_join_ok": {
        "uz": "Tekshirildi. Botdan foydalanishingiz mumkin.",
        "ru": "Проверено. Теперь можно пользоваться ботом.",
        "en": "Checked. You can use the bot now.",
    },
    "force_join_ok_message": {
        "uz": "✅ A’zolik tasdiqlandi. Davom etishingiz mumkin.",
        "ru": "✅ Участие подтверждено. Можно продолжать.",
        "en": "✅ Membership confirmed. You can continue.",
    },
    "private_chat_only": {
        "uz": "Bot faqat shaxsiy chatda ishlaydi.",
        "ru": "Бот работает только в личном чате.",
        "en": "This bot works only in private chat.",
    },
})

def validate_texts() -> list[str]:
    errors: list[str] = []
    for key, translations in TEXTS.items():
        for lang in ("uz", "ru", "en"):
            if lang not in translations:
                errors.append(f"Missing key '{key}' for language '{lang}'")
    for key, translations in BUTTONS.items():
        for lang in ("uz", "ru", "en"):
            if lang not in translations:
                errors.append(f"Missing button '{key}' for language '{lang}'")
    return errors

TEXTS.update({
    "movie_temporarily_unavailable": {
        "uz": "⚠️ Kino hozircha yuborilmadi. Fayl vaqtincha mavjud emas, admin tekshiradi.",
        "ru": "⚠️ Фильм временно недоступен. Файл сейчас не отправляется, админ проверит.",
        "en": "⚠️ Movie temporarily unavailable. The file could not be delivered and admin should check it.",
    },
})


# v31 public-room list UX polish
TEXTS.update({
    "rooms_menu": {
        "uz": "👥 <b>Xonalar</b>\n\nPublic xonalar — ro‘yxatdan tanlab kiriladi.\nPrivate xonalar — faqat kod bilan.\n\nNima qilamiz?",
        "ru": "👥 <b>Комнаты</b>\n\nPublic комнаты — выбираются из списка.\nPrivate комнаты — только по коду.\n\nЧто делаем?",
        "en": "👥 <b>Rooms</b>\n\nPublic rooms are chosen from a list.\nPrivate rooms are joined by code.\n\nWhat do you want to do?",
    },
    "room_public_list": {
        "uz": "🌍 <b>Public xonalar</b>\n\nO‘zingizga yoqqan xonani tanlang. Har bir qatorda a’zolar soni va kayfiyat ko‘rsatilgan.\n\n{rooms}",
        "ru": "🌍 <b>Public комнаты</b>\n\nВыберите комнату. В каждой строке показаны участники и настроение.\n\n{rooms}",
        "en": "🌍 <b>Public rooms</b>\n\nChoose the room you want. Each row shows members and vibe.\n\n{rooms}",
    },
    "room_public_line": {
        "uz": "{n}. <b>{title}</b> — {count}/{limit} — {mood}",
        "ru": "{n}. <b>{title}</b> — {count}/{limit} — {mood}",
        "en": "{n}. <b>{title}</b> — {count}/{limit} — {mood}",
    },
    "room_public_hint": {
        "uz": "Tanlashni xohlamasangiz, pastdagi tasodifiy kirish tugmasini bosing.",
        "ru": "Если не хотите выбирать, нажмите случайный вход ниже.",
        "en": "If you do not want to choose, use the random join button below.",
    },
    "room_no_public": {
        "uz": "Hozircha mos public xona yo‘q. Plus/Pro bo‘lsangiz, o‘zingiz public xona ochib birinchilardan bo‘ling.",
        "ru": "Пока нет подходящей public комнаты. Если у вас Plus/Pro, создайте свою public комнату первым.",
        "en": "No matching public room right now. If you have Plus/Pro, create a public room and be first.",
    },
    "room_selected_unavailable": {
        "uz": "Bu xona hozir mavjud emas yoki to‘lib qolgan. Ro‘yxatni yangilab ko‘ring.",
        "ru": "Эта комната уже недоступна или заполнена. Обновите список.",
        "en": "That room is no longer available or is full. Refresh the list.",
    },
    "room_joined_named": {
        "uz": "✅ <b>{title}</b> xonasiga kirdingiz.\n\nEndi oddiy xabar yozing — u xonadagi a’zolarga anonim yuboriladi.",
        "ru": "✅ Вы вошли в комнату <b>{title}</b>.\n\nПишите обычное сообщение — оно анонимно уйдёт участникам комнаты.",
        "en": "✅ You joined <b>{title}</b>.\n\nType a normal message — it will be sent anonymously to room members.",
    },
})

BUTTONS.update({
    "join_public_room": {"uz": "🌍 Public xonalar", "ru": "🌍 Public комнаты", "en": "🌍 Public rooms"},
})


# v32 deploy monetization polish: Free usable with friction, Plus comfort, Pro host/no limits.
TEXTS.update({'premium_page': {'uz': '⭐ <b>Plus / Pro</b>\n\nHozirgi reja: <b>{plan}</b>{expires}\n\n<b>Free</b> — 1-1 anonim suhbat, kuniga {free_skips} skip, kuniga {free_movies} kino. Reklama ko‘proq. Xona ochish yo‘q.\n\n<b>Plus</b> — kamroq reklama, kuniga {plus_skips} skip, oyiga {plus_movies} kino, 7 kishilik anonim kino xonasi.\n\n<b>Pro</b> — reklamasiz, kuniga {pro_skips} skip, deyarli cheksiz kino, 14 kishilik katta anonim kino xonasi va host imkoniyatlari.', 'ru': '⭐ <b>Plus / Pro</b>\n\nТекущий план: <b>{plan}</b>{expires}\n\n<b>Free</b> — 1-на-1 анонимный чат, {free_skips} skip/день, {free_movies} фильм/день. Больше рекламы. Создание комнат недоступно.\n\n<b>Plus</b> — меньше рекламы, {plus_skips} skip/день, {plus_movies} фильмов/месяц, анонимная кино-комната до 7 человек.\n\n<b>Pro</b> — без рекламы, {pro_skips} skip/день, почти безлимитные фильмы, большая анонимная кино-комната до 14 человек и возможности host.', 'en': '⭐ <b>Plus / Pro</b>\n\nCurrent plan: <b>{plan}</b>{expires}\n\n<b>Free</b> — 1-to-1 anonymous chat, {free_skips} skips/day, {free_movies} movie/day. More ads. No room creation.\n\n<b>Plus</b> — fewer ads, {plus_skips} skips/day, {plus_movies} movies/month, 7-person anonymous movie room.\n\n<b>Pro</b> — no ads, {pro_skips} skips/day, almost unlimited movies, 14-person anonymous movie room and host powers.'}, 'premium_required': {'uz': '🔒 Anonim kino xonasi ochish Plus/Pro imkoniyati.\n\nPlus: 7 kishilik xona.\nPro: 14 kishilik katta xona va reklamasiz foydalanish.', 'ru': '🔒 Создание анонимной кино-комнаты доступно в Plus/Pro.\n\nPlus: комната до 7 человек.\nPro: большая комната до 14 человек и без рекламы.', 'en': '🔒 Creating anonymous movie rooms is a Plus/Pro feature.\n\nPlus: 7-person room.\nPro: 14-person room and no ads.'}, 'skip_limit': {'uz': 'Bugungi bepul skiplar tugadi: {used}/{limit}.\n\nPlus bilan kuniga 25 ta, Pro bilan 100 ta skip olasiz.', 'ru': 'Сегодняшние бесплатные skip закончились: {used}/{limit}.\n\nPlus даёт 25 skip/день, Pro — 100 skip/день.', 'en': "Today's free skips are over: {used}/{limit}.\n\nPlus gives 25 skips/day, Pro gives 100 skips/day."}, 'movie_limit': {'uz': 'Bugungi bepul kino limiti tugadi: {used}/{limit} ({period}).\n\nPlus bilan oyiga 150 ta kino, Pro bilan deyarli cheksiz kino ochiladi. Suhbat davom etadi.', 'ru': 'Бесплатный лимит фильмов закончился: {used}/{limit} ({period}).\n\nPlus открывает 150 фильмов/месяц, Pro — почти безлимит. Чат продолжается.', 'en': 'Your free movie limit is over: {used}/{limit} ({period}).\n\nPlus unlocks 150 movies/month, Pro is almost unlimited. Chat continues.'}, 'room_join_premium_required': {'uz': '🔐 Private xona kodlari Plus/Pro uchun. Public xonalarni esa mavjud bo‘lsa Free rejada ham sinab ko‘rishingiz mumkin.', 'ru': '🔐 Private комнаты по коду доступны в Plus/Pro. Public комнаты можно пробовать и на Free, если они есть.', 'en': '🔐 Private room codes are for Plus/Pro. Public rooms can be tried on Free when available.'}, 'upgrade_after_ad': {'uz': 'Reklamalarni kamaytirish uchun Plus, butunlay o‘chirish uchun Pro oling.', 'ru': 'Plus уменьшает рекламу, Pro полностью убирает её.', 'en': 'Plus reduces ads. Pro removes them completely.'}, 'upgrade_skip_limit': {'uz': 'Tez-tez boshqa suhbatdosh qidirmoqchimisiz? Plus/Pro ko‘proq skip beradi.', 'ru': 'Хотите чаще менять собеседника? Plus/Pro дают больше skip.', 'en': 'Want to find new partners faster? Plus/Pro gives more skips.'}, 'upgrade_movie_limit': {'uz': 'Ko‘proq kino ochish uchun Plus, deyarli cheksiz foydalanish uchun Pro oling.', 'ru': 'Для большего количества фильмов возьмите Plus, для почти безлимита — Pro.', 'en': 'Get Plus for more movies, or Pro for almost unlimited access.'}, 'upgrade_room_create': {'uz': 'Eng kuchli funksiya — private anonim kino xonasi. Plus: 7 kishi. Pro: 14 kishi.', 'ru': 'Самая сильная функция — private анонимная кино-комната. Plus: 7 человек. Pro: 14 человек.', 'en': 'The strongest feature is a private anonymous movie room. Plus: 7 people. Pro: 14 people.'}, 'waiting_timeout': {'uz': '🕐 Hozir mos suhbatdosh topilmadi. Qayta urinib ko‘ring yoki public xonalarga kiring — kechki aktiv vaqtlarda tezroq topiladi.\n\nPlus/Pro reklama va limitlarda ancha qulayroq.', 'ru': '🕐 Сейчас подходящий собеседник не найден. Попробуйте ещё раз или зайдите в public комнаты — вечером обычно быстрее.\n\nPlus/Pro намного удобнее по рекламе и лимитам.', 'en': '🕐 No matching partner right now. Try again or join public rooms — evening active hours usually match faster.\n\nPlus/Pro is much smoother with ads and limits.'}, 'premium_payment_note': {'uz': '💳 To‘lov Telegram Stars orqali avtomatik ishlaydi. To‘lov muvaffaqiyatli bo‘lsa, Plus/Pro darhol ochiladi.', 'ru': '💳 Оплата автоматически проходит через Telegram Stars. После успешной оплаты Plus/Pro включается сразу.', 'en': '💳 Payment works automatically through Telegram Stars. After successful payment, Plus/Pro activates immediately.'}})
