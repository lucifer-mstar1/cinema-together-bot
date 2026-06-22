from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
if len(sys.argv) != 2:
    raise SystemExit("Usage: python scripts/restore_sqlite.py backups/file.db")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./cinema_together.db")
if not DATABASE_URL.startswith("sqlite"):
    raise SystemExit("restore_sqlite.py only supports SQLite DATABASE_URL")
target = Path(DATABASE_URL.split("///", 1)[-1])
source = Path(sys.argv[1])
if not source.exists():
    raise SystemExit(f"Backup not found: {source}")
if target.exists():
    target.rename(target.with_suffix(target.suffix + ".before_restore"))
shutil.copy2(source, target)
print(f"Restored {source} -> {target}")
