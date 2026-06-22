import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import init_db


async def main():
    # Production-safe seed: create/verify schema only.
    # Movies should be added by admins through the bot, not inserted as fake codes.
    await init_db()
    print("Seed complete. No sample movies inserted. Add real movies from the admin panel.")


if __name__ == "__main__":
    asyncio.run(main())
