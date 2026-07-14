from __future__ import annotations

from dataclasses import dataclass
import os
from typing import final

from pydantic import BaseModel, ConfigDict
import requests


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str
    content: str
    ordinal: int


@dataclass(frozen=True, slots=True)
class Conversation:
    npc_id: str
    messages: tuple[ChatMessage, ...]


@dataclass(frozen=True, slots=True)
class QuestProgress:
    quest_id: str
    quest_state: str
    allowed_hint_level: int


class MessagePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: str
    content: str
    ordinal: int


class ConversationPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    npc_id: str
    messages: tuple[MessagePayload, ...] = ()


class QuestProgressPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    quest_id: str
    quest_state: str
    allowed_hint_level: int


class GameStatePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    quests: tuple[QuestProgressPayload, ...] = ()


@final
class GameApiClient:
    def __init__(self, base_url: str | None = None) -> None:
        self._base_url: str = (base_url or os.getenv("GAME_API_URL", "http://127.0.0.1:8000/api")).rstrip("/")
        self._session: requests.Session = requests.Session()
        self._session_token: str | None = None

    def bootstrap(self) -> None:
        response = self._session.post(
            f"{self._base_url}/sessions/bootstrap",
            headers=self._session_headers(),
            timeout=10,
        )
        response.raise_for_status()
        issued = response.cookies.get("hazel_session")
        if issued is not None:
            self._session_token = issued

    def _session_headers(self) -> dict[str, str]:
        if self._session_token is None:
            return {}
        return {"Cookie": f"hazel_session={self._session_token}"}

    def get_conversation(self, npc_id: str) -> Conversation:
        response = self._session.get(
            f"{self._base_url}/game/npcs/{npc_id}/conversation",
            headers=self._session_headers(),
            timeout=10,
        )
        response.raise_for_status()
        payload = ConversationPayload.model_validate_json(response.text)
        messages = tuple(
            ChatMessage(
                role=message.role,
                content=message.content,
                ordinal=message.ordinal,
            )
            for message in payload.messages
        )
        return Conversation(npc_id=payload.npc_id, messages=messages)

    def get_quest_progress(self) -> tuple[QuestProgress, ...]:
        response = self._session.get(
            f"{self._base_url}/game/state",
            headers=self._session_headers(),
            timeout=10,
        )
        response.raise_for_status()
        payload = GameStatePayload.model_validate_json(response.text)
        return tuple(
            QuestProgress(item.quest_id, item.quest_state, item.allowed_hint_level)
            for item in payload.quests
        )

    def create_turn(self, npc_id: str, quest_id: str, content: str, idempotency_key: str) -> None:
        response = self._session.post(
            f"{self._base_url}/game/turns",
            headers={"Idempotency-Key": idempotency_key, **self._session_headers()},
            json={"npc_id": npc_id, "quest_id": quest_id, "content": content},
            timeout=180,
        )
        response.raise_for_status()
