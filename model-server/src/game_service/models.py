from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    kind: Mapped[str] = mapped_column(String(16), default="guest")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id"), unique=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


class BrowserSession(Base):
    __tablename__ = "browser_sessions"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AdminAuditEvent(Base):
    __tablename__ = "admin_audit_events"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    admin_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    action: Mapped[str] = mapped_column(String(80))
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(128))
    event_metadata: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FullKnowledgeDocument(Base):
    __tablename__ = "full_knowledge_documents"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    document_metadata: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))


class Save(Base):
    __tablename__ = "saves"
    __table_args__ = (UniqueConstraint("player_id", "slot_index"),)

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id"), index=True)
    slot_index: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(80), default="헤이즐 마을 기록")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("save_id", "npc_id"),)

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    save_id: Mapped[UUID] = mapped_column(ForeignKey("saves.id"), index=True)
    npc_id: Mapped[str] = mapped_column(String(64))


class TurnAttempt(Base):
    __tablename__ = "turn_attempts"
    __table_args__ = (UniqueConstraint("conversation_id", "idempotency_key"),)

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(24), default="llm_pending")
    failure_code: Mapped[str | None] = mapped_column(String(64))
    quest_decision: Mapped[dict[str, str] | None] = mapped_column(JSONB)


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("conversation_id", "ordinal"),)

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"), index=True)
    turn_attempt_id: Mapped[UUID] = mapped_column(ForeignKey("turn_attempts.id"))
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    ordinal: Mapped[int] = mapped_column(Integer)


class QuestProgress(Base):
    __tablename__ = "quest_progress"
    __table_args__ = (UniqueConstraint("save_id", "quest_id"),)

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    save_id: Mapped[UUID] = mapped_column(ForeignKey("saves.id"), index=True)
    quest_id: Mapped[str] = mapped_column(String(64))
    quest_state: Mapped[str] = mapped_column(String(32))
    allowed_hint_level: Mapped[int] = mapped_column(Integer)


class ObservedClue(Base):
    __tablename__ = "observed_clues"
    __table_args__ = (UniqueConstraint("save_id", "quest_id", "clue_id"),)

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    save_id: Mapped[UUID] = mapped_column(ForeignKey("saves.id"), index=True)
    quest_id: Mapped[str] = mapped_column(String(64))
    clue_id: Mapped[str] = mapped_column(String(64))


class NpcMemorySummary(Base):
    __tablename__ = "npc_memory_summaries"
    __table_args__ = (UniqueConstraint("save_id", "npc_id"),)

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    save_id: Mapped[UUID] = mapped_column(ForeignKey("saves.id"), index=True)
    npc_id: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text, default="")
    recent_turn_count: Mapped[int] = mapped_column(Integer, default=0)
    max_memory_count: Mapped[int] = mapped_column(Integer, default=40)
