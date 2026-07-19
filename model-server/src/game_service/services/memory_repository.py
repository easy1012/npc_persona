from __future__ import annotations

from typing import final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.game_service.models import Message, NpcMemorySummary
from src.game_service.services.memory_service import (
    DEFAULT_MEMORY_THRESHOLD,
    MemoryCheckpoint,
    MemoryMessage,
    MemoryRole,
    MemoryScope,
)


class UnsupportedMemoryRoleError(RuntimeError):
    def __init__(self, role: str) -> None:
        super().__init__(f"unsupported persisted memory role: {role}")


def _memory_role(role: str) -> MemoryRole:
    match role:
        case "user":
            return "user"
        case "assistant":
            return "assistant"
        case unsupported:
            raise UnsupportedMemoryRoleError(unsupported)


@final
class SqlAlchemyMemoryStore:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _checkpoint_row(self, scope: MemoryScope) -> NpcMemorySummary:
        _ = await self._db.execute(
            pg_insert(NpcMemorySummary)
            .values(
                save_id=scope.save_id,
                npc_id=scope.npc_id,
                summary="",
                recent_turn_count=0,
                max_memory_count=DEFAULT_MEMORY_THRESHOLD,
                summarized_through_ordinal=-1,
            )
            .on_conflict_do_nothing(index_elements=[NpcMemorySummary.save_id, NpcMemorySummary.npc_id])
        )
        row = await self._db.scalar(
            select(NpcMemorySummary).where(
                NpcMemorySummary.save_id == scope.save_id,
                NpcMemorySummary.npc_id == scope.npc_id,
            )
        )
        if row is None:
            raise RuntimeError("memory checkpoint upsert did not return a row")
        return row

    async def load_checkpoint(self, scope: MemoryScope) -> MemoryCheckpoint:
        row = await self._checkpoint_row(scope)
        return MemoryCheckpoint(
            summary=row.summary,
            summarized_through_ordinal=row.summarized_through_ordinal,
            max_memory_count=row.max_memory_count,
        )

    async def load_messages(
        self,
        scope: MemoryScope,
        *,
        after_ordinal: int,
        exclude_turn_attempt_id: UUID | None = None,
    ) -> tuple[MemoryMessage, ...]:
        query = (
            select(Message)
            .where(
                Message.conversation_id == scope.conversation_id,
                Message.ordinal > after_ordinal,
                Message.role.in_(("user", "assistant")),
            )
            .order_by(Message.ordinal)
        )
        if exclude_turn_attempt_id is not None:
            query = query.where(Message.turn_attempt_id != exclude_turn_attempt_id)
        rows = (await self._db.scalars(query)).all()
        await self._db.commit()
        return tuple(
            MemoryMessage(role=_memory_role(row.role), content=row.content, ordinal=row.ordinal)
            for row in rows
        )

    async def save_compaction(
        self,
        scope: MemoryScope,
        *,
        expected_through_ordinal: int,
        summary: str,
        through_ordinal: int,
        recent_message_count: int,
    ) -> bool:
        row = await self._db.scalar(
            select(NpcMemorySummary)
            .where(
                NpcMemorySummary.save_id == scope.save_id,
                NpcMemorySummary.npc_id == scope.npc_id,
            )
            .with_for_update()
        )
        if row is None or row.summarized_through_ordinal != expected_through_ordinal:
            await self._db.rollback()
            return False
        row.summary = summary
        row.summarized_through_ordinal = through_ordinal
        row.recent_turn_count = recent_message_count
        await self._db.commit()
        return True

    async def save_recent_message_count(self, scope: MemoryScope, count: int) -> None:
        row = await self._checkpoint_row(scope)
        row.recent_turn_count = count
        await self._db.commit()
