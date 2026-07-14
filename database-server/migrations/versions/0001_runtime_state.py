from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "0001_runtime_state"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    _ = op.create_table(
        "players",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False, server_default="guest"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
    )
    _ = op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("player_id", sa.Uuid(), sa.ForeignKey("players.id"), nullable=False, unique=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    _ = op.create_table(
        "browser_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("player_id", sa.Uuid(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_browser_sessions_player_id", "browser_sessions", ["player_id"])
    _ = op.create_table(
        "admin_audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("admin_account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("resource_type", sa.String(80), nullable=False),
        sa.Column("resource_id", sa.String(128), nullable=False),
        sa.Column("event_metadata", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_admin_audit_events_admin_account_id", "admin_audit_events", ["admin_account_id"])
    _ = op.create_table(
        "saves",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("player_id", sa.Uuid(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("slot_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("name", sa.String(80), nullable=False, server_default="헤이즐 마을 기록"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("player_id", "slot_index"),
    )
    op.create_index("ix_saves_player_id", "saves", ["player_id"])
    _ = op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("save_id", sa.Uuid(), sa.ForeignKey("saves.id"), nullable=False),
        sa.Column("npc_id", sa.String(64), nullable=False),
        sa.UniqueConstraint("save_id", "npc_id"),
    )
    op.create_index("ix_conversations_save_id", "conversations", ["save_id"])
    _ = op.create_table(
        "turn_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="llm_pending"),
        sa.Column("failure_code", sa.String(64), nullable=True),
        sa.Column("quest_decision", JSONB(), nullable=True),
        sa.UniqueConstraint("conversation_id", "idempotency_key"),
    )
    op.create_index("ix_turn_attempts_conversation_id", "turn_attempts", ["conversation_id"])
    _ = op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("turn_attempt_id", sa.Uuid(), sa.ForeignKey("turn_attempts.id"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.UniqueConstraint("conversation_id", "ordinal"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    _ = op.create_table(
        "quest_progress",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("save_id", sa.Uuid(), sa.ForeignKey("saves.id"), nullable=False),
        sa.Column("quest_id", sa.String(64), nullable=False),
        sa.Column("quest_state", sa.String(32), nullable=False),
        sa.Column("allowed_hint_level", sa.Integer(), nullable=False),
        sa.UniqueConstraint("save_id", "quest_id"),
    )
    op.create_index("ix_quest_progress_save_id", "quest_progress", ["save_id"])
    _ = op.create_table(
        "observed_clues",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("save_id", sa.Uuid(), sa.ForeignKey("saves.id"), nullable=False),
        sa.Column("quest_id", sa.String(64), nullable=False),
        sa.Column("clue_id", sa.String(64), nullable=False),
        sa.UniqueConstraint("save_id", "quest_id", "clue_id"),
    )
    op.create_index("ix_observed_clues_save_id", "observed_clues", ["save_id"])
    _ = op.create_table(
        "npc_memory_summaries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("save_id", sa.Uuid(), sa.ForeignKey("saves.id"), nullable=False),
        sa.Column("npc_id", sa.String(64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("recent_turn_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_memory_count", sa.Integer(), nullable=False, server_default="40"),
        sa.UniqueConstraint("save_id", "npc_id"),
    )
    op.create_index("ix_npc_memory_summaries_save_id", "npc_memory_summaries", ["save_id"])


def downgrade() -> None:
    op.drop_index("ix_npc_memory_summaries_save_id", table_name="npc_memory_summaries")
    op.drop_table("npc_memory_summaries")
    op.drop_index("ix_observed_clues_save_id", table_name="observed_clues")
    op.drop_table("observed_clues")
    op.drop_index("ix_quest_progress_save_id", table_name="quest_progress")
    op.drop_table("quest_progress")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_turn_attempts_conversation_id", table_name="turn_attempts")
    op.drop_table("turn_attempts")
    op.drop_index("ix_conversations_save_id", table_name="conversations")
    op.drop_table("conversations")
    op.drop_index("ix_saves_player_id", table_name="saves")
    op.drop_table("saves")
    op.drop_index("ix_admin_audit_events_admin_account_id", table_name="admin_audit_events")
    op.drop_table("admin_audit_events")
    op.drop_index("ix_browser_sessions_player_id", table_name="browser_sessions")
    op.drop_table("browser_sessions")
    op.drop_table("accounts")
    op.drop_table("players")
