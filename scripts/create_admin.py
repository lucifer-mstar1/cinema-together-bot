import argparse
import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import SessionLocal, init_db
from app.services import get_or_create_user


class TgUser:
    def __init__(self, telegram_id: int, username: str | None):
        self.id = telegram_id
        self.username = username
        self.first_name = username or "Admin"
        self.language_code = "uz"


async def main(telegram_id: int, username: str | None):
    await init_db()
    async with SessionLocal() as session:
        user = await get_or_create_user(session, TgUser(telegram_id, username))
        user.is_admin = True
        await session.commit()
    print(f"Admin ready: {telegram_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("telegram_id", type=int)
    parser.add_argument("--username", default=None)
    args = parser.parse_args()
    asyncio.run(main(args.telegram_id, args.username))
