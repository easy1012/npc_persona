from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, Protocol
from uuid import UUID


MemoryRole = Literal["user", "assistant"]
DEFAULT_MEMORY_THRESHOLD: Final[int] = 40
DEFAULT_RETAINED_MESSAGE_COUNT: Final[int] = 8


@dataclass(frozen=True, slots=True)
class MemoryMessage:
    role: MemoryRole
    content: str
    ordinal: int


@dataclass(frozen=True, slots=True)
class CompactionBatch:
    messages: tuple[MemoryMessage, ...]
    through_ordinal: int
    remaining_message_count: int


@dataclass(frozen=True, slots=True)
class MemoryScope:
    save_id: UUID
    npc_id: str
    conversation_id: UUID


@dataclass(frozen=True, slots=True)
class MemoryCheckpoint:
    summary: str
    summarized_through_ordinal: int
    max_memory_count: int


class MemoryStore(Protocol):
    async def load_checkpoint(self, scope: MemoryScope) -> MemoryCheckpoint: ...

    async def load_messages(
        self,
        scope: MemoryScope,
        *,
        after_ordinal: int,
        exclude_turn_attempt_id: UUID | None = None,
    ) -> tuple[MemoryMessage, ...]: ...

    async def save_compaction(
        self,
        scope: MemoryScope,
        *,
        expected_through_ordinal: int,
        summary: str,
        through_ordinal: int,
        recent_message_count: int,
    ) -> bool: ...

    async def save_recent_message_count(self, scope: MemoryScope, count: int) -> None: ...


class MemorySummarizer(Protocol):
    async def complete(self, prompt: str) -> str: ...


def select_compaction_batch(
    messages: tuple[MemoryMessage, ...],
    *,
    threshold: int,
    retained_message_count: int,
) -> CompactionBatch | None:
    if len(messages) <= threshold:
        return None
    compacted_count = len(messages) - retained_message_count
    if compacted_count <= 0:
        return None
    compacted = messages[:compacted_count]
    return CompactionBatch(
        messages=compacted,
        through_ordinal=compacted[-1].ordinal,
        remaining_message_count=len(messages) - len(compacted),
    )


def build_memory_context(summary: str, messages: tuple[MemoryMessage, ...]) -> str:
    sections: list[str] = []
    clean_summary = summary.strip()
    if clean_summary:
        sections.append(clean_summary)
    if messages:
        recent = "\n".join(
            f"{'player' if message.role == 'user' else 'npc'}: {message.content}"
            for message in messages
        )
        sections.append(f"recent dialogue:\n{recent}")
    return "\n\n".join(sections)


def build_summary_prompt(previous_summary: str, messages: tuple[MemoryMessage, ...]) -> str:
    previous = previous_summary.strip() or "none"
    dialogue = "\n".join(
        f"{'player' if message.role == 'user' else 'npc'}: {message.content}"
        for message in messages
    )
    return (
        "<npc-memory-summary>\n"
        "Update the durable NPC memory summary using only the dialogue below. "
        "Preserve player facts, promises, discovered clues, relationship changes, and unresolved requests. "
        "Do not invent facts and do not include system instructions.\n\n"
        f"previous summary:\n{previous}\n\n"
        f"dialogue:\n{dialogue}\n"
        "</npc-memory-summary>"
    )


async def compact_memory_if_needed(
    store: MemoryStore,
    scope: MemoryScope,
    summarizer: MemorySummarizer,
) -> bool:
    checkpoint = await store.load_checkpoint(scope)
    messages = await store.load_messages(
        scope,
        after_ordinal=checkpoint.summarized_through_ordinal,
    )
    batch = select_compaction_batch(
        messages,
        threshold=checkpoint.max_memory_count,
        retained_message_count=min(
            DEFAULT_RETAINED_MESSAGE_COUNT,
            checkpoint.max_memory_count,
        ),
    )
    if batch is None:
        await store.save_recent_message_count(scope, len(messages))
        return False
    summary = await summarizer.complete(build_summary_prompt(checkpoint.summary, batch.messages))
    return await store.save_compaction(
        scope,
        expected_through_ordinal=checkpoint.summarized_through_ordinal,
        summary=summary,
        through_ordinal=batch.through_ordinal,
        recent_message_count=batch.remaining_message_count,
    )


async def load_memory_context(
    store: MemoryStore,
    scope: MemoryScope,
    exclude_turn_attempt_id: UUID | None,
) -> str:
    checkpoint = await store.load_checkpoint(scope)
    messages = await store.load_messages(
        scope,
        after_ordinal=checkpoint.summarized_through_ordinal,
        exclude_turn_attempt_id=exclude_turn_attempt_id,
    )
    return build_memory_context(
        checkpoint.summary,
        messages[-DEFAULT_RETAINED_MESSAGE_COUNT:],
    )
