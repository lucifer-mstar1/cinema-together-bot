from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "backups"))
BACKUP_DIR.mkdir(exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./cinema_together.db")
stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

if DATABASE_URL.startswith("sqlite"):
    db_path = DATABASE_URL.split("///", 1)[-1]
    source = Path(db_path)
    if not source.exists():
        raise SystemExit(f"SQLite DB not found: {source}")
    target = BACKUP_DIR / f"cinema_together_{stamp}.db"
    shutil.copy2(source, target)
    print(f"SQLite backup written to {target}")
elif DATABASE_URL.startswith("postgresql"):
    target = BACKUP_DIR / f"cinema_together_{stamp}.sql"
    cmd = ["pg_dump", DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"), "-f", str(target)]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)
    print(f"PostgreSQL backup written to {target}")
else:
    print(f"Unsupported DATABASE_URL: {DATABASE_URL}", file=sys.stderr)
    raise SystemExit(1)
