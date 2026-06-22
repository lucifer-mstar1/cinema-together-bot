# CinemaTogether v33 Production Guide

This version is intended as a real production base, not only a beta. The bot now uses durable database state for waiting/matching recovery, Redis-backed FSM, DB-backed pending watch intents, and Alembic migrations.

## Local mode

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python scripts/seed.py
python scripts/create_admin.py YOUR_TELEGRAM_ID --username your_username
python run.py
```

Local SQLite is still fine:

```env
APP_ENV=development
BOT_MODE=polling
DATABASE_URL=sqlite+aiosqlite:///./cinema_together.db
AUTO_CREATE_SCHEMA=true
REDIS_URL=redis://localhost:6379/0
MOCK_PAYMENTS=false
```

## Production requirements

Use PostgreSQL and Redis before public launch:

```env
APP_ENV=production
BOT_MODE=polling
DATABASE_URL=postgresql+asyncpg://cinema:strong-password@localhost:5432/cinema_together
REDIS_URL=redis://localhost:6379/0
AUTO_CREATE_SCHEMA=false
MOCK_PAYMENTS=false
REPORT_MATCH_AVOID_DAYS=14
```

Run migrations before starting the service:

```bash
alembic upgrade head
```

`AUTO_CREATE_SCHEMA=true` is intentionally blocked in production. Schema changes should go through migrations.

Payment/subscription safety in this build:

- Successful Telegram Stars payments are applied with a conditional pending → succeeded update.
- Duplicate/replayed successful-payment updates return the existing subscription without adding days twice.
- Free/Plus/Pro movie unlock counters are consumed atomically before delivery and refunded if Telegram delivery fully fails.
- Active 1:1 match ownership is guarded by `active_match_participants.user_id` uniqueness.

## Webhook mode

```env
APP_ENV=production
BOT_MODE=webhook
WEBHOOK_BASE_URL=https://your-domain.com
WEBHOOK_PATH=/telegram/webhook
WEBHOOK_SECRET=use-a-long-random-string
DATABASE_URL=postgresql+asyncpg://cinema:strong-password@db:5432/cinema_together
REDIS_URL=redis://redis:6379/0
AUTO_CREATE_SCHEMA=false
MOCK_PAYMENTS=false
```

Start with:

```bash
uvicorn app.webhook_server:app --host 0.0.0.0 --port 8000
```

Nginx example is in `deploy/nginx-cinema-together.conf`. Do not run polling and webhook for the same token at the same time.

## Forced join gate

Final force-join polish in v30:

- Required groups/channels are join gates only; normal bot commands/buttons are ignored inside groups.
- The join screen refreshes after every check and only keeps missing channels/groups visible.
- Malformed invite links fail startup validation instead of creating broken Telegram buttons.


```env
# Listing at least one required chat activates the gate automatically.
FORCE_JOIN_ENABLED=false
FORCE_JOIN_CHATS=@your_public_channel,-1001234567890|https://t.me/+privateInvite|Private Group
FORCE_JOIN_CHANNELS=@second_channel
FORCE_JOIN_GROUPS=-1009876543210|https://t.me/+anotherInvite|VIP Group
FORCE_JOIN_STRICT=true
FORCE_JOIN_CHECK_TTL=0
FORCE_JOIN_FAIL_OPEN=false
```

The bot must be a member/admin of every configured chat. Users must join all listed channels/groups and, with strict mode on, leaving during use blocks their next private update. Private invite links alone cannot be verified by Telegram; use `-100...|invite_link|Title`. Pending `/start watch_CODE` intents are saved before the gate, so users do not lose movie deep links after joining.

## Safety policy

Pro users can send richer media, but links, usernames, phone numbers, and contact extraction are blocked until a future mutual-consent exchange flow is implemented. Manual blocks are permanent. Report-only match avoidance is time-limited by `REPORT_MATCH_AVOID_DAYS`.

## Launch checklist

- Use a fresh production BotFather token.
- Use PostgreSQL and Redis.
- Run `alembic upgrade head`.
- Set `AUTO_CREATE_SCHEMA=false`.
- Set `MOCK_PAYMENTS=false`.
- Change `WEBHOOK_SECRET`.
- Test forced join with a non-admin account.
- Test `/health`, `/admin_stats`, reports, movie upload, payment, rooms, and matching.
- Enable backups.


Note: Required groups/channels are join gates only. The bot ignores normal commands/buttons inside groups so the group stays a normal community chat. Use the bot in private chat.


## v33 monetization polish

Final deploy defaults use Free as usable but limited, Plus as comfortable, and Pro as host/no-limits:

```env
FREE_AD_INTERVAL=2
PLUS_AD_INTERVAL=5
FREE_DAILY_MOVIE_UNLOCKS=3
ALLOW_FREE_ROOM_JOIN=true
MOCK_PAYMENTS=false
```

Free users can try public rooms when available, but creating rooms and private invite-code rooms remain Plus/Pro features. User-facing mock/test payment buttons are hidden in the final UI.
