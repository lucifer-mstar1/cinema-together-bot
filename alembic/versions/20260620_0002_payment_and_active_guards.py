"""payment and active match hardening guards

Revision ID: 20260620_0002
Revises: 20260619_0001
Create Date: 2026-06-20
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260620_0002"
down_revision = "20260619_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()

    usage_monthly = sa.Table(
        "usage_monthly",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("movie_unlocks_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "month", name="uq_usage_user_month"),
    )
    usage_monthly.create(bind, checkfirst=True)
    sa.Index("ix_usage_monthly_month", usage_monthly.c.month).create(bind, checkfirst=True)

    active_participants = sa.Table(
        "active_match_participants",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_active_match_participant_user"),
    )
    active_participants.create(bind, checkfirst=True)
    sa.Index("ix_active_match_participants_match_id", active_participants.c.match_id).create(bind, checkfirst=True)
    sa.Index("ix_active_match_participants_user_id", active_participants.c.user_id).create(bind, checkfirst=True)

    # Backfill ownership rows for active matches created before this migration.
    matches = sa.table(
        "matches",
        sa.column("id", sa.Integer()),
        sa.column("user_a_id", sa.Integer()),
        sa.column("user_b_id", sa.Integer()),
        sa.column("status", sa.String()),
        sa.column("created_at", sa.DateTime()),
    )
    rows = list(bind.execute(sa.select(matches.c.id, matches.c.user_a_id, matches.c.user_b_id, matches.c.created_at).where(matches.c.status == "active")))
    for match_id, user_a_id, user_b_id, created_at in rows:
        for user_id in (user_a_id, user_b_id):
            try:
                bind.execute(active_participants.insert().values(match_id=match_id, user_id=user_id, created_at=created_at))
            except Exception:
                # If a user somehow already has an active owner row, keep the
                # first one. Runtime code will resolve future sessions safely.
                pass


def downgrade() -> None:
    bind = op.get_bind()
    sa.Table("active_match_participants", sa.MetaData()).drop(bind, checkfirst=True)
    sa.Table("usage_monthly", sa.MetaData()).drop(bind, checkfirst=True)
