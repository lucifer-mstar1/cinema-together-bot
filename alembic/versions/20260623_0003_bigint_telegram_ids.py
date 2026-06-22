"""convert telegram ids to bigint

Revision ID: 20260623_0003
Revises: 20260620_0002
Create Date: 2026-06-23
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260623_0003"
down_revision = "20260620_0002"
branch_labels = None
depends_on = None


COLUMNS = [
    ("users", "telegram_id"),
    ("telegram_entitlements", "telegram_id"),
    ("telegram_blocks", "blocker_telegram_id"),
    ("telegram_blocks", "blocked_telegram_id"),
    ("telegram_restrictions", "telegram_id"),
    ("report_strikes", "reported_telegram_id"),
    ("report_strikes", "reporter_telegram_id"),
    ("reserved_anon_names", "user_telegram_id"),
    ("ad_campaigns", "source_chat_id"),
    ("waiting_queue", "telegram_id"),
    ("waiting_queue", "chat_id"),
    ("pending_watch_intents", "telegram_id"),
]


def upgrade() -> None:
    for table, column in COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )


def downgrade() -> None:
    for table, column in COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
