# CinemaTogether Bot — v33 Public Room UX Final Release

This build keeps the chat-first CinemaTogether concept and hardens the v23 smart-random matching code for a real production product foundation.

## v33 public room UX final changes

- Public rooms now show a selectable list instead of silently auto-joining a room.
- Users see room title, member count, and mood before joining.
- A random public-room button is still available for fast entry.
- Private rooms still use invite codes.

## v30 final changes

- Forced join now activates automatically when required chats are listed, supports unlimited required channels/groups, exempts admins, and strict-checks every private update so users who leave are blocked again.

- Bot ignores normal commands/buttons inside required groups/channels, so your required group stays a real group and does not become the bot UI.
- Force-join check now refreshes the join screen and shows only the still-missing channels/groups; already joined ones disappear from the buttons.
- Force-join config now rejects malformed links like `https://t.me/https://...` before launch.
- Moved waiting queue and active chat/room recovery to durable database state.
- Added Redis FSM storage; `REDIS_URL` is required for real bot runs so onboarding/admin states survive restarts.
- Added Alembic migration support; production should run `alembic upgrade head` instead of auto-creating schema.
- Payment completion is now idempotent: duplicate Telegram successful-payment updates cannot double-extend Plus/Pro.
- Movie unlock counters are now atomically consumed with refund on delivery failure.
- Active matches now have DB-level participant ownership guards to prevent duplicate active chats.
- Redis connectivity is health-checked at startup so broken FSM state fails fast instead of failing during user updates.
- Idle movie code typing now works directly from channel posts.
- Added DB-backed pending `/start watch_CODE` preservation so forced join cannot lose movie deep-link intent.
- Report-only match avoidance is now time-limited by `REPORT_MATCH_AVOID_DAYS`; manual blocks remain permanent.
- Pro/Admin no longer bypass contact/link moderation inside anonymous chats. Richer media stays premium, contact extraction does not.
- Admin movie upload now accepts legal URL, Telegram video, or video-document.
- Movie delivery failures no longer show raw Telegram file IDs to users.
- Main menu is simplified around Find Partner, Movie Codes, Rooms, Premium, and Profile.
- Removed duplicate room creation handler; room creation now always uses the intended FSM flow.
- Standardized runtime comparisons on naive UTC timestamps across services, bot handlers, and tests.
- Added a matching lock to prevent duplicate simultaneous matches in a single-process deployment.
- Mood compatibility is now enforced: `casual` can match any mood, while non-casual moods match only the same mood or `casual`.
- Matching now randomly chooses among top-scoring candidates instead of always picking the first candidate.
- Immediate same-pair rematches stay blocked, but pairs can naturally meet again after each person has had other chats.
- `/clean` no longer deletes financial records or paid access. Payment rows remain and plans restore from `TelegramEntitlement`.
- Report strikes now count only within a 7-day window.
- Moderation is stricter against obfuscated contacts while avoiding false positives for years, prices, runtimes, and normal movie chat.
- Admin movie creation asks code, title, type, language, year, then video/link, and generates clean channel posts.
- Admins in `ADMIN_IDS` no longer need a restart-sensitive password session.
- Startup validates translation coverage before the bot/webhook starts.
- Admin stats now include active Plus/Pro and Stars collected today.
- Rooms now support member reporting.
- Webhook mode can use durable DB/Redis-backed state when production env is configured correctly.

## Important production note

Production requires PostgreSQL + Redis + Alembic migrations. Local SQLite is still supported for development database storage, but Redis is still required for FSM state. Public launch should use:

```env
APP_ENV=production
DATABASE_URL=postgresql+asyncpg://cinema:strong-password@db:5432/cinema_together
REDIS_URL=redis://redis:6379/0
AUTO_CREATE_SCHEMA=false
MOCK_PAYMENTS=false
```

Before starting the bot in production, run:

```bash
alembic upgrade head
```

## Important clean limitation

Telegram bots do not have a real “clear this whole private chat exactly like the user deleted the bot” API. This build keeps the fast bot-side reset and deletion behavior. Messages Telegram refuses to delete, usually old messages or client-side history, cannot be removed by bot code.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

Minimum `.env`:

```env
BOT_TOKEN=YOUR_BOT_TOKEN
ADMIN_IDS=YOUR_TELEGRAM_ID
DATABASE_URL=sqlite+aiosqlite:///./cinema_together.db
DEFAULT_LANGUAGE=uz
MOVIES_CHANNEL_URL=https://t.me/YOUR_REAL_MOVIE_CHANNEL
MOCK_PAYMENTS=false
DELETE_CLEANUP_MESSAGES=true
CLEAN_DELETE_WINDOW=450
CLEAN_FINAL_MESSAGE=false
FREE_AD_INTERVAL=2
PLUS_AD_INTERVAL=5
SAME_PAIR_REMATCH_AFTER_CHATS=1
REDIS_URL=redis://localhost:6379/0
AUTO_CREATE_SCHEMA=false
# Optional: force users to join channels/groups before using the bot
FORCE_JOIN_ENABLED=false
FORCE_JOIN_CHATS=
FORCE_JOIN_CHANNELS=
FORCE_JOIN_GROUPS=
FORCE_JOIN_STRICT=true
FORCE_JOIN_CHECK_TTL=0
FORCE_JOIN_FAIL_OPEN=false
```

Then run:

```bash
alembic upgrade head
python scripts/seed.py
python run.py
```

## Admin usage

Send `/start` from the Telegram account whose ID is in `ADMIN_IDS`. The admin panel opens automatically; no password re-authentication is required after restart.

Admin panel buttons:

- Add movie
- Movies
- Delete movie
- Channel post
- Ads
- Reports
- Stats
- Admin language

## Add movie flow

1. Press **Add movie**
2. Enter a code or press `AUTO`
3. Send a legal watch URL, Telegram **video**, or Telegram video-document
4. The bot saves and publishes automatically, using the caption/text as the title when available

## Delete movie flow

1. Press **Movies** to see the numbered list
2. Press **Delete movie**
3. Type the movie number, for example `1`
4. Numbers are recalculated automatically after deletion

## Channel flow

Configure one of these:

```env
MOVIES_CHANNEL_URL=https://t.me/YOUR_REAL_MOVIE_CHANNEL
MOVIES_CHANNEL_USERNAME=YOUR_REAL_MOVIE_CHANNEL
```

Users press **Movie list** in the main menu to open the channel.

Admin presses **Channel post** and chooses a movie number to get a copy-ready channel post with deep link.


## Force users to join channels/groups

Gate is controlled from `.env`. If you put at least one required chat in `FORCE_JOIN_CHATS`, `FORCE_JOIN_CHANNELS`, or `FORCE_JOIN_GROUPS`, the gate activates automatically. Users must join **all** configured chats before they can use the bot, and strict mode checks again on every private update so users who leave are blocked again.

```env
FORCE_JOIN_ENABLED=false
FORCE_JOIN_CHATS=@your_public_channel,-1001234567890|https://t.me/+privateInvite|Private Group
FORCE_JOIN_CHANNELS=@second_channel,https://t.me/third_channel
FORCE_JOIN_GROUPS=-1009876543210|https://t.me/+anotherInvite|VIP Group
FORCE_JOIN_STRICT=true
FORCE_JOIN_CHECK_TTL=0
FORCE_JOIN_FAIL_OPEN=false
```

Notes:

- Admin IDs and admin usernames are exempt from the join gate.
- Add the bot to every required channel/group, preferably as admin, so Telegram allows `getChatMember` checks.
- Public channels/groups can be configured as `@username` or `https://t.me/username`.
- Private groups/channels cannot be verified from invite link alone; use numeric chat ID plus invite link: `-100...|https://t.me/+invite|Title`.
- All three lists are merged and deduplicated, so you can require as many channels/groups as you want.
- `FORCE_JOIN_STRICT=true` + `FORCE_JOIN_CHECK_TTL=0` means leaving during use blocks the next message/button.
- `FORCE_JOIN_FAIL_OPEN=false` is strict; users stay blocked if Telegram cannot verify membership.

## Payments

Payments use Telegram Stars (`XTR`). User presses Plus/Pro, Telegram confirms payment, and the bot activates the plan automatically.

Final UI uses real Telegram Stars payment buttons. Keep `MOCK_PAYMENTS=false` for deploy. Admin-only mock commands can still be enabled locally if you intentionally set `MOCK_PAYMENTS=true` in development.

Payment records are permanent. `/clean` resets the user profile but preserves payment history and restores active entitlement on the next `/start`.

## Tests

```bash
pytest -q
```

Expected result in this build: all tests pass.


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
