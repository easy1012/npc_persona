from __future__ import annotations

import unittest
from typing import final
from uuid import UUID

from sqlalchemy.dialects import postgresql

from src.game_service.models import NpcMemorySummary
from src.game_service.services.memory_service import (
    MemoryCheckpoint,
    MemoryMessage,
    MemoryScope,
    build_memory_context,
    compact_memory_if_needed,
    select_compaction_batch,
)
from src.game_service.services.turn_service import conversation_append_lock


@final
class FakeMemoryStore:
    def __init__(self, checkpoint: MemoryCheckpoint, messages: tuple[MemoryMessage, ...]) -> None:
        self.checkpoint = checkpoint
        self.messages = messages
        self.saved_summary: str | None = None
        self.saved_through_ordinal: int | None = None
        self.recent_message_count: int | None = None

    async def load_checkpoint(self, scope: MemoryScope) -> MemoryCheckpoint:
        _ = scope
        return self.checkpoint

    async def load_messages(
        self,
        scope: MemoryScope,
        *,
        after_ordinal: int,
        exclude_turn_attempt_id: UUID | None = None,
    ) -> tuple[MemoryMessage, ...]:
        _ = scope, exclude_turn_attempt_id
        return tuple(message for message in self.messages if message.ordinal > after_ordinal)

    async def save_compaction(
        self,
        scope: MemoryScope,
        *,
        expected_through_ordinal: int,
        summary: str,
        through_ordinal: int,
        recent_message_count: int,
    ) -> bool:
        _ = scope
        if self.checkpoint.summarized_through_ordinal != expected_through_ordinal:
            return False
        self.saved_summary = summary
        self.saved_through_ordinal = through_ordinal
        self.recent_message_count = recent_message_count
        return True

    async def save_recent_message_count(self, scope: MemoryScope, count: int) -> None:
        _ = scope
        self.recent_message_count = count


class FakeSummarizer:
    async def complete(self, prompt: str) -> str:
        _ = prompt
        return "플레이어는 숲 방향의 발자국을 확인했다."


class MemoryServiceTest(unittest.TestCase):
    def test_assistant_ordinal_is_allocated_under_conversation_lock(self) -> None:
        statement = conversation_append_lock(UUID("11111111-1111-1111-1111-111111111111"))
        sql = str(statement.compile(dialect=postgresql.dialect()))
        self.assertIn("FOR UPDATE", sql)

    def test_memory_checkpoint_schema_tracks_compaction_cursor(self) -> None:
        columns = NpcMemorySummary.__table__.columns
        self.assertIn("summarized_through_ordinal", columns)
        self.assertIn("updated_at", columns)

    def test_memory_compaction_selects_old_messages_and_retains_recent_window(self) -> None:
        messages = tuple(
            MemoryMessage(role="user" if ordinal % 2 == 0 else "assistant", content=str(ordinal), ordinal=ordinal)
            for ordinal in range(12)
        )
        batch = select_compaction_batch(messages, threshold=10, retained_message_count=4)
        self.assertIsNotNone(batch)
        assert batch is not None
        self.assertEqual(tuple(range(8)), tuple(message.ordinal for message in batch.messages))
        self.assertEqual(7, batch.through_ordinal)
        self.assertEqual(4, batch.remaining_message_count)

    def test_memory_compaction_does_not_run_at_threshold(self) -> None:
        messages = tuple(
            MemoryMessage(role="user", content=str(ordinal), ordinal=ordinal)
            for ordinal in range(10)
        )
        self.assertIsNone(select_compaction_batch(messages, threshold=10, retained_message_count=4))

    def test_memory_state_is_isolated_per_npc(self) -> None:
        save_id = UUID("11111111-1111-1111-1111-111111111111")
        lumi_scope = MemoryScope(
            save_id=save_id,
            npc_id="mage_lumi",
            conversation_id=UUID("22222222-2222-2222-2222-222222222222"),
        )
        rio_scope = MemoryScope(
            save_id=save_id,
            npc_id="patrol_leader_rio",
            conversation_id=UUID("33333333-3333-3333-3333-333333333333"),
        )
        self.assertNotEqual(lumi_scope, rio_scope)

    def test_memory_context_restores_summary_and_recent_dialogue(self) -> None:
        recent = (
            MemoryMessage(role="user", content="발자국을 봤어.", ordinal=8),
            MemoryMessage(role="assistant", content="숲 방향이군요.", ordinal=9),
        )
        context = build_memory_context("이전에는 버섯을 조사했다.", recent)
        self.assertIn("이전에는 버섯을 조사했다.", context)
        self.assertIn("player: 발자국을 봤어.", context)
        self.assertIn("npc: 숲 방향이군요.", context)


class MemoryCompactionTest(unittest.IsolatedAsyncioTestCase):
    async def test_memory_compaction_persists_summary_when_threshold_is_reached(self) -> None:
        scope = MemoryScope(
            save_id=UUID("11111111-1111-1111-1111-111111111111"),
            npc_id="patrol_leader_rio",
            conversation_id=UUID("22222222-2222-2222-2222-222222222222"),
        )
        checkpoint = MemoryCheckpoint(summary="", summarized_through_ordinal=-1, max_memory_count=2)
        messages = tuple(
            MemoryMessage(role="user" if ordinal % 2 == 0 else "assistant", content=str(ordinal), ordinal=ordinal)
            for ordinal in range(4)
        )
        store = FakeMemoryStore(checkpoint, messages)
        compacted = await compact_memory_if_needed(store, scope, FakeSummarizer())
        self.assertTrue(compacted)
        self.assertEqual("플레이어는 숲 방향의 발자국을 확인했다.", store.saved_summary)
        self.assertEqual(1, store.saved_through_ordinal)
        self.assertEqual(2, store.recent_message_count)

    async def test_memory_compaction_is_idempotent_when_checkpoint_advanced(self) -> None:
        scope = MemoryScope(
            save_id=UUID("11111111-1111-1111-1111-111111111111"),
            npc_id="mage_lumi",
            conversation_id=UUID("33333333-3333-3333-3333-333333333333"),
        )
        checkpoint = MemoryCheckpoint(summary="old", summarized_through_ordinal=1, max_memory_count=2)
        messages = (
            MemoryMessage(role="user", content="2", ordinal=2),
            MemoryMessage(role="assistant", content="3", ordinal=3),
        )
        store = FakeMemoryStore(checkpoint, messages)
        compacted = await compact_memory_if_needed(store, scope, FakeSummarizer())
        self.assertFalse(compacted)
        self.assertIsNone(store.saved_summary)
        self.assertEqual(2, store.recent_message_count)
