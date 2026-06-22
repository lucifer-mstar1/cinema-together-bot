"""real product schema baseline

Revision ID: 20260619_0001
Revises:
Create Date: 2026-06-19
"""
from __future__ import annotations

from alembic import op

revision = "20260619_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Baseline migration for the current production schema. Existing dev setups
    # can keep AUTO_CREATE_SCHEMA=true; production should run `alembic upgrade head`.
    from app import models  # noqa: F401
    from app.db import Base

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from app import models  # noqa: F401
    from app.db import Base

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
