"""Initial schema — conversation history + competitor profiles + post schedule

Revision ID: 001
Revises:
Create Date: 2026-03-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Conversation Sessions ───────────────────────────────────────────────
    op.create_table(
        "conversation_sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("message_count", sa.Integer, default=0),
        sa.Column("metadata", sa.JSON, nullable=True),
    )

    # ─── Conversation Messages ───────────────────────────────────────────────
    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("conversation_sessions.id", ondelete="CASCADE")),
        sa.Column("role", sa.String(16)),         # user | assistant
        sa.Column("content", sa.Text),
        sa.Column("tokens", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_messages_session_id", "conversation_messages", ["session_id"])

    # ─── Competitor Profiles ─────────────────────────────────────────────────
    op.create_table(
        "competitor_profiles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), unique=True, nullable=False),
        sa.Column("website", sa.String(512)),
        sa.Column("facebook_page", sa.String(256), nullable=True),
        sa.Column("industry", sa.String(64), default="general"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Competitor Snapshots ────────────────────────────────────────────────
    op.create_table(
        "competitor_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("competitor_id", sa.Integer, sa.ForeignKey("competitor_profiles.id", ondelete="CASCADE")),
        sa.Column("snapshot_data", sa.JSON),
        sa.Column("changes_detected", sa.Boolean, default=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_snapshots_competitor_id", "competitor_snapshots", ["competitor_id"])

    # ─── Scheduled Posts ────────────────────────────────────────────────────
    op.create_table(
        "scheduled_posts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("platform", sa.String(32)),
        sa.Column("content", sa.Text),
        sa.Column("scheduled_time", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(16), default="pending"),   # pending|posted|failed
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_posts_status", "scheduled_posts", ["status"])
    op.create_index("ix_posts_scheduled_time", "scheduled_posts", ["scheduled_time"])

    # ─── Trend Scan History ──────────────────────────────────────────────────
    op.create_table(
        "trend_scans",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("industry", sa.String(64)),
        sa.Column("articles_found", sa.Integer, default=0),
        sa.Column("is_crisis", sa.Boolean, default=False),
        sa.Column("crisis_severity", sa.String(16), nullable=True),
        sa.Column("trend_summary", sa.Text, nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_trends_industry", "trend_scans", ["industry"])


def downgrade() -> None:
    op.drop_table("trend_scans")
    op.drop_table("scheduled_posts")
    op.drop_table("competitor_snapshots")
    op.drop_table("competitor_profiles")
    op.drop_table("conversation_messages")
    op.drop_table("conversation_sessions")
