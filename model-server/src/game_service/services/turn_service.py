from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Protocol
from uuid import UUID

from pydantic import ValidationError
import requests
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.game_service.models import Conversation, Message, QuestProgress, TurnAttempt
from src.game_service.services.memory_repository import SqlAlchemyMemoryStore
from src.game_service.services.memory_service import (
    MemoryScope,
    compact_memory_if_needed,
    load_memory_context,
)
from src.game_service.services.retrieval_service import GraphDriver, retrieve_hybrid_knowledge
from src.streamlit.prompting import build_prompt
from src.streamlit.quest_types import NPC_METADATA, NPC_NAMES


logger = logging.getLogger(__name__)


class LlmClient(Protocol):
    async def complete(self, prompt: str) -> str: ...

    async def embed(self, text: str) -> list[float]: ...


@dataclass(frozen=True, slots=True)
class PendingTurn:
    idempotency_key: str
    status: str = "llm_pending"


async def complete_pending_turn(
    pending: PendingTurn,
    prompt: str,
    llm_client: LlmClient,
) -> tuple[str, str]:
    _ = pending
    response = await llm_client.complete(prompt)
    return ("succeeded", response)


FAILED_STATUS = "failed"


def conversation_append_lock(conversation_id: UUID) -> Select[tuple[UUID]]:
    return select(Conversation.id).where(Conversation.id == conversation_id).with_for_update()


def npc_prompt_profile(npc_id: str) -> dict[str, object]:
    return {"name": NPC_NAMES[npc_id], "role": NPC_METADATA[npc_id].player_role}


async def complete_persisted_turn(
    db: AsyncSession,
    attempt_id: UUID,
    conversation: Conversation,
    quest_id: str,
    user_message: str,
    graph: GraphDriver,
    llm_client: LlmClient,
) -> TurnAttempt:
    attempt = await db.get(TurnAttempt, attempt_id)
    if attempt is None:
        raise ValueError("turn attempt no longer exists")
    if attempt.status == "succeeded":
        return attempt
    attempt.status = "llm_pending"
    attempt.failure_code = None
    await db.commit()
    memory_store = SqlAlchemyMemoryStore(db)
    memory_scope = MemoryScope(
        save_id=conversation.save_id,
        npc_id=conversation.npc_id,
        conversation_id=conversation.id,
    )
    try:
        progress = await db.scalar(
            select(QuestProgress).where(
                QuestProgress.save_id == conversation.save_id,
                QuestProgress.quest_id == quest_id,
            )
        )
        quest_state = progress.quest_state if progress is not None else "not_started"
        hint_level = progress.allowed_hint_level if progress is not None else 0
        decision = attempt.quest_decision or {}
        guidance = str(decision.get("guidance", ""))
        profile = npc_prompt_profile(conversation.npc_id)
        player_role = str(profile["role"])
        answer_reveal_allowed = bool(decision.get("reveal_truth_ids")) or quest_state == "solved"
        embedding = await llm_client.embed(user_message) if answer_reveal_allowed else []
        knowledge = await retrieve_hybrid_knowledge(
            db,
            graph,
            conversation.npc_id,
            quest_id,
            player_role,
            quest_state,
            hint_level,
            answer_reveal_allowed,
            user_message,
            embedding,
        )
        context = await load_memory_context(memory_store, memory_scope, attempt.id)
        chunks = list(knowledge.graph_chunks)
        chunks.extend({"title": "마을 기록", "text": document} for document in knowledge.full_documents)
        prompt = build_prompt(
            npc=profile,
            chunks=chunks,
            user_message=user_message,
            quest_state=quest_state,
            player_role=player_role,
            allowed_hint_level=hint_level,
            conversation_context=context,
            quest_guidance=guidance,
            answer_reveal_allowed=answer_reveal_allowed,
        )
        await db.commit()
        answer = await llm_client.complete(prompt)
        _ = await db.execute(conversation_append_lock(conversation.id))
        ordinal = await db.scalar(
            select(func.coalesce(func.max(Message.ordinal), -1)).where(
                Message.conversation_id == conversation.id
            )
        )
        db.add(
            Message(
                conversation_id=conversation.id,
                turn_attempt_id=attempt.id,
                role="assistant",
                content=answer,
                ordinal=(ordinal if ordinal is not None else -1) + 1,
            )
        )
        attempt.status = "succeeded"
        await db.commit()
    except Exception as error:
        logger.exception(
            "turn completion failed",
            extra={"attempt_id": str(attempt_id), "npc_id": conversation.npc_id},
        )
        await db.rollback()
        attempt = await db.get(TurnAttempt, attempt_id)
        if attempt is None:
            raise
        attempt.status = FAILED_STATUS
        attempt.failure_code = type(error).__name__[:64]
        await db.commit()
    if attempt.status == "succeeded":
        try:
            _ = await compact_memory_if_needed(memory_store, memory_scope, llm_client)
        except (requests.RequestException, ValidationError, SQLAlchemyError, RuntimeError, ValueError):
            logger.exception(
                "memory compaction failed",
                extra={"attempt_id": str(attempt_id), "npc_id": conversation.npc_id},
            )
            await db.rollback()
            reloaded_attempt = await db.get(TurnAttempt, attempt_id)
            if reloaded_attempt is None:
                raise RuntimeError("completed turn disappeared after memory rollback")
            attempt = reloaded_attempt
            await db.refresh(conversation)
    return attempt
