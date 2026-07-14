from __future__ import annotations

from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, status
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.game_service.clients import VllmClient, get_graph_driver, get_vllm_client
from src.game_service.db import database_session
from src.game_service.models import Conversation, Message, QuestProgress, TurnAttempt
from src.game_service.schemas import (
    ConversationResponse,
    GameStateResponse,
    MessageResponse,
    QuestProgressResponse,
    TurnRequest,
    TurnResponse,
)
from src.game_service.services.session_service import SessionPrincipal, resolve_session
from src.game_service.services.turn_service import complete_persisted_turn
from src.game_service.services.retrieval_service import GraphDriver


router = APIRouter(prefix="/game", tags=["game"])


async def _principal(
    db: AsyncSession,
    token: str | None,
) -> SessionPrincipal:
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "session required")
    principal = await resolve_session(db, token)
    if principal is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid session")
    return principal


def _message_role(role: str) -> Literal["user", "assistant"]:
    if role == "user" or role == "assistant":
        return role
    raise ValueError(f"unsupported message role: {role}")


def _turn_status(value: str) -> Literal["llm_pending", "succeeded", "failed"]:
    if value in {"llm_pending", "succeeded", "failed"}:
        return cast(Literal["llm_pending", "succeeded", "failed"], value)
    raise ValueError(f"unsupported turn status: {value}")


def should_complete_attempt(attempt: TurnAttempt, *, created: bool) -> bool:
    return created or attempt.status == "failed"


async def _conversation(db: AsyncSession, save_id: UUID, npc_id: str) -> Conversation:
    conversation_id = await db.scalar(
        pg_insert(Conversation)
        .values(save_id=save_id, npc_id=npc_id)
        .on_conflict_do_nothing(index_elements=[Conversation.save_id, Conversation.npc_id])
        .returning(Conversation.id)
    )
    conversation = (
        await db.get(Conversation, conversation_id)
        if conversation_id is not None
        else await db.scalar(
            select(Conversation).where(Conversation.save_id == save_id, Conversation.npc_id == npc_id)
        )
    )
    if conversation is None:
        raise RuntimeError("conversation upsert did not return a row")
    return conversation


async def _response(db: AsyncSession, conversation: Conversation) -> ConversationResponse:
    messages = tuple(
        MessageResponse(role=_message_role(message.role), content=message.content, ordinal=message.ordinal)
        for message in (
            await db.scalars(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.ordinal)
            )
        ).all()
    )
    return ConversationResponse(npc_id=conversation.npc_id, messages=messages)


@router.get("/npcs/{npc_id}/conversation", response_model=ConversationResponse)
async def get_conversation(
    npc_id: str,
    db: Annotated[AsyncSession, Depends(database_session)],
    hazel_session: Annotated[str | None, Cookie()] = None,
) -> ConversationResponse:
    principal = await _principal(db, hazel_session)
    conversation = await _conversation(db, principal.save_id, npc_id)
    await db.commit()
    return await _response(db, conversation)


@router.get("/state", response_model=GameStateResponse)
async def get_game_state(
    db: Annotated[AsyncSession, Depends(database_session)],
    hazel_session: Annotated[str | None, Cookie()] = None,
) -> GameStateResponse:
    principal = await _principal(db, hazel_session)
    progress = (
        await db.scalars(
            select(QuestProgress)
            .where(QuestProgress.save_id == principal.save_id)
            .order_by(QuestProgress.quest_id)
        )
    ).all()
    return GameStateResponse(
        quests=tuple(
            QuestProgressResponse(
                quest_id=item.quest_id,
                quest_state=item.quest_state,
                allowed_hint_level=item.allowed_hint_level,
            )
            for item in progress
        )
    )


@router.post("/turns", response_model=TurnResponse, status_code=202)
async def create_turn(
    turn: TurnRequest,
    db: Annotated[AsyncSession, Depends(database_session)],
    graph: Annotated[GraphDriver, Depends(get_graph_driver)],
    llm_client: Annotated[VllmClient, Depends(get_vllm_client)],
    idempotency_key: str = Header(alias="Idempotency-Key"),
    hazel_session: Annotated[str | None, Cookie()] = None,
) -> TurnResponse:
    principal = await _principal(db, hazel_session)
    conversation = await _conversation(db, principal.save_id, turn.npc_id)
    _ = await db.execute(select(Conversation.id).where(Conversation.id == conversation.id).with_for_update())
    progress = await db.scalar(
        select(QuestProgress).where(
            QuestProgress.save_id == principal.save_id,
            QuestProgress.quest_id == turn.quest_id,
        )
    )
    if progress is None:
        db.add(
            QuestProgress(
                save_id=principal.save_id,
                quest_id=turn.quest_id,
                quest_state="in_progress",
                allowed_hint_level=1,
            )
        )
    attempt = await db.scalar(
        select(TurnAttempt).where(
            TurnAttempt.conversation_id == conversation.id,
            TurnAttempt.idempotency_key == idempotency_key,
        )
    )
    created_attempt = attempt is None
    if created_attempt:
        attempt = TurnAttempt(
            conversation_id=conversation.id,
            idempotency_key=idempotency_key,
            quest_decision={"quest_id": turn.quest_id},
        )
        db.add(attempt)
        await db.flush()
        last_ordinal = await db.scalar(
            select(func.coalesce(func.max(Message.ordinal), -1)).where(
                Message.conversation_id == conversation.id
            )
        )
        db.add(
            Message(
                conversation_id=conversation.id,
                turn_attempt_id=attempt.id,
                role="user",
                content=turn.content,
                ordinal=(last_ordinal if last_ordinal is not None else -1) + 1,
            )
        )
        await db.commit()
        persisted_content = turn.content
    else:
        persisted_content = await db.scalar(
            select(Message.content).where(
                Message.turn_attempt_id == attempt.id,
                Message.role == "user",
            )
        )
        if persisted_content is None:
            raise RuntimeError("turn attempt is missing its user message")
    if should_complete_attempt(attempt, created=created_attempt):
        attempt = await complete_persisted_turn(
            db,
            attempt.id,
            conversation,
            turn.quest_id,
            persisted_content,
            graph,
            llm_client,
        )
    return TurnResponse(
        turn_attempt_id=attempt.id,
        status=_turn_status(attempt.status),
        conversation=await _response(db, conversation),
    )
