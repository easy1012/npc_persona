from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Literal["user", "assistant"]
    content: str
    ordinal: int


class ConversationResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    npc_id: str
    messages: tuple[MessageResponse, ...] = ()


class TurnRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    npc_id: str
    quest_id: str
    content: str = Field(min_length=1, max_length=4000)


class TurnResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    turn_attempt_id: UUID
    status: Literal["llm_pending", "succeeded", "failed"]
    conversation: ConversationResponse


class QuestProgressResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    quest_id: str
    quest_state: str
    allowed_hint_level: int


class GameStateResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    quests: tuple[QuestProgressResponse, ...] = ()
