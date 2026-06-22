from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

# Simple built-in filters. Replace/extend these lists before public launch.
BAD_WORDS = {
    "fuck", "bitch", "shit", "asshole",
    "сука", "бля", "нах",
    "jalab", "haromi", "ahmoq",
}

URL_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|telegram\.dog/|bit\.ly/|tinyurl\.com/|(?:[A-Za-z0-9-]+\.)+(?:com|net|org|uz|ru|io|me|co|app|dev|site|online|link)\b)", re.IGNORECASE)
USERNAME_RE = re.compile(r"(?<![A-Za-z0-9_])@[A-Za-z0-9_]{3,32}\b")
SPACED_USERNAME_RE = re.compile(r"@\s+[A-Za-z0-9_]{3,32}", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?998[\s\-()\W]*(?:\d[\s\-()\W]*){9}|\+?[78][\s\-()\W]*(?:\d[\s\-()\W]*){10}|(?:9[01345789]|88|33|55|77)[\s\-()\W]*(?:\d[\s\-()\W]*){7})(?!\d)",
    re.IGNORECASE,
)
WRITTEN_LINK_RE = re.compile(
    r"t(?:elegram)?\s*(?:[.\-:]|dot)\s*me\s*/|"
    r"telegram\s*[:.]\s*(?:me|com|dog)\s*/|"
    r"telegram\s*[:.]\s*@?[A-Za-z0-9_]{3,32}|"
    r"tg\s*[:.]\s*[A-Za-z]",
    re.IGNORECASE,
)
BAD_WORD_RE = re.compile(r"\b(" + "|".join(re.escape(w) for w in sorted(BAD_WORDS, key=len, reverse=True)) + r")\b", re.IGNORECASE)


def normalize_text(text: str) -> str:
    text = "".join(c for c in text if unicodedata.category(c) not in ("Cf", "Cc"))
    replacements = {"O": "0", "l": "1", "I": "1", "о": "0", "О": "0"}
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


@dataclass(frozen=True)
class ModerationResult:
    allowed: bool
    category: str | None = None
    reason: str | None = None
    severity: int = 0


def check_message(text: str) -> ModerationResult:
    text = text or ""
    normalized = normalize_text(text)
    if len(text) > 1500:
        return ModerationResult(False, "too_long", "message_too_long", 1)
    if URL_RE.search(text) or URL_RE.search(normalized) or WRITTEN_LINK_RE.search(text) or WRITTEN_LINK_RE.search(normalized):
        return ModerationResult(False, "link", "links_are_not_allowed", 1)
    if USERNAME_RE.search(text) or SPACED_USERNAME_RE.search(text) or PHONE_RE.search(normalized):
        return ModerationResult(False, "personal_data", "personal_contact_is_not_allowed", 1)
    if BAD_WORD_RE.search(text):
        return ModerationResult(False, "bad_word", "insult_or_bad_word", 2)
    return ModerationResult(True)
