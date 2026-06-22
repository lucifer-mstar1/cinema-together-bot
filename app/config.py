from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


_PLACEHOLDER_FORCE_JOIN_VALUES = {
    "@your_channel",
    "your_channel",
    "https://t.me/your_channel",
    "-1001234567890",
    "-1001234567890|https://t.me/+inviteLink|Private Group",
    "https://t.me/+inviteLink",
}


def _is_placeholder_force_join_item(value: str) -> bool:
    clean = (value or "").strip()
    if not clean:
        return True
    lowered = clean.lower()
    if clean in _PLACEHOLDER_FORCE_JOIN_VALUES:
        return True
    return any(token in lowered for token in ("your_channel", "invitelink", "example", "change-me"))


class Settings(BaseSettings):
    bot_token: str = ""
    admin_ids: list[int] = []
    admin_usernames: list[str] = []

    app_env: str = "development"
    log_level: str = "INFO"
    log_file: str = "logs/cinema_together.log"

    bot_mode: str = "polling"
    drop_pending_updates: bool = True

    database_url: str = "sqlite+aiosqlite:///./cinema_together.db"
    auto_create_schema: bool = True
    redis_url: str = ""

    webhook_base_url: str = ""
    webhook_path: str = "/telegram/webhook"
    webhook_secret: str = "change-me-long-random-secret"
    webapp_host: str = "0.0.0.0"
    webapp_port: int = 8000

    default_language: str = "uz"
    movies_channel_url: str = ""
    movies_channel_username: str = ""
    delete_cleanup_messages: bool = True
    clean_delete_window: int = 450
    clean_final_message: bool = False
    free_ad_interval: int = 2
    plus_ad_interval: int = 5
    same_pair_rematch_after_chats: int = 1
    report_match_avoid_days: int = 14

    # Optional forced channel/group membership gate.
    # Any non-empty FORCE_JOIN_CHATS / FORCE_JOIN_CHANNELS / FORCE_JOIN_GROUPS value
    # activates the gate automatically; FORCE_JOIN_ENABLED remains as an explicit override.
    # Accepted item examples, comma/semicolon/newline separated:
    #   @public_channel
    #   https://t.me/public_channel
    #   -1001234567890|https://t.me/+privateInvite|Private group title
    # For private groups/channels Telegram requires the numeric -100... chat ID for checks.
    force_join_enabled: bool = False
    force_join_chats: list[str] = []
    force_join_channels: list[str] = []
    force_join_groups: list[str] = []
    force_join_check_ttl: int = 0
    force_join_strict: bool = True
    force_join_fail_open: bool = False

    free_daily_skips: int = 5
    plus_daily_skips: int = 25
    pro_daily_skips: int = 100

    free_daily_movie_unlocks: int = 3
    plus_monthly_movie_unlocks: int = 150
    pro_daily_movie_unlocks: int = 999

    allow_free_room_join: bool = True

    mock_payments: bool = False
    plus_1m_stars: int = 50
    plus_3m_stars: int = 110
    plus_6m_stars: int = 250
    plus_12m_stars: int = 550
    pro_1m_stars: int = 150
    pro_3m_stars: int = 330
    pro_6m_stars: int = 750
    pro_12m_stars: int = 1500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        enable_decoding=False,
    )

    @property
    def webhook_url(self) -> str:
        if not self.webhook_base_url:
            return ""
        return self.webhook_base_url.rstrip("/") + self.webhook_path

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def mock_payments_enabled(self) -> bool:
        return bool(self.mock_payments and not self.is_production)

    @property
    def force_join_items(self) -> list[str]:
        items: list[str] = []
        for group in (self.force_join_chats, self.force_join_channels, self.force_join_groups):
            for item in group or []:
                clean = str(item).strip()
                if clean and clean not in items:
                    items.append(clean)
        return items

    @property
    def force_join_active(self) -> bool:
        return bool(self.force_join_enabled or self.force_join_items)

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, int):
            return [value]
        if isinstance(value, str):
            return [int(x.strip()) for x in value.split(",") if x.strip()]
        if isinstance(value, (list, tuple, set)):
            return [int(x) for x in value]
        return [int(value)]


    @staticmethod
    def _parse_chat_list(value):
        if value is None or value == "":
            return []
        if isinstance(value, str):
            raw = value.replace("\n", ",").replace(";", ",")
            return [x.strip() for x in raw.split(",") if x.strip() and not _is_placeholder_force_join_item(x)]
        if isinstance(value, (list, tuple, set)):
            return [str(x).strip() for x in value if str(x).strip() and not _is_placeholder_force_join_item(str(x))]
        clean = str(value).strip()
        return [] if _is_placeholder_force_join_item(clean) else [clean]

    @field_validator("force_join_chats", "force_join_channels", "force_join_groups", mode="before")
    @classmethod
    def parse_force_join_chat_lists(cls, value):
        return cls._parse_chat_list(value)

    @field_validator("admin_usernames", mode="before")
    @classmethod
    def parse_admin_usernames(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [x.strip().lstrip("@").lower() for x in value.split(",") if x.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(x).strip().lstrip("@").lower() for x in value if str(x).strip()]
        return [str(value).strip().lstrip("@").lower()]

    @field_validator("bot_mode")
    @classmethod
    def validate_bot_mode(cls, value: str) -> str:
        value = (value or "polling").lower().strip()
        if value not in {"polling", "webhook"}:
            raise ValueError("BOT_MODE must be polling or webhook")
        return value

    @field_validator("default_language")
    @classmethod
    def validate_default_language(cls, value: str) -> str:
        return value if value in {"uz", "ru", "en"} else "uz"

    def ensure_runtime_dirs(self) -> None:
        if self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_runtime_dirs()
    return settings
