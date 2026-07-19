from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import cast, final

from neo4j import GraphDatabase
from pydantic import BaseModel, ConfigDict
import requests

from src.game_service.config import get_settings
from src.game_service.services.retrieval_service import GraphDriver


class ChatMessagePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str


class ChatChoicePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    message: ChatMessagePayload


class ChatCompletionPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    choices: tuple[ChatChoicePayload, ...]


class EmbeddingItemPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    embedding: list[float]


class EmbeddingPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    data: tuple[EmbeddingItemPayload, ...]


@final
class VllmClient:
    def __init__(self, chat_url: str, embedding_url: str, model: str, embedding_model: str) -> None:
        self._chat_url = chat_url
        self._embedding_url = embedding_url
        self._model = model
        self._embedding_model = embedding_model

    async def complete(self, prompt: str) -> str:
        return await asyncio.to_thread(self._complete_sync, prompt)

    async def embed(self, text: str) -> list[float]:
        return await asyncio.to_thread(self._embed_sync, text)

    def _complete_sync(self, prompt: str) -> str:
        response = requests.post(
            self._chat_url,
            json={"model": self._model, "messages": [{"role": "user", "content": prompt}]},
            timeout=180,
        )
        response.raise_for_status()
        payload = ChatCompletionPayload.model_validate_json(response.text)
        if not payload.choices:
            raise ValueError("vLLM returned no completion choices")
        return payload.choices[0].message.content

    def _embed_sync(self, text: str) -> list[float]:
        response = requests.post(
            self._embedding_url,
            json={"model": self._embedding_model, "input": text},
            timeout=60,
        )
        response.raise_for_status()
        payload = EmbeddingPayload.model_validate_json(response.text)
        if not payload.data:
            raise ValueError("embedding endpoint returned no vectors")
        return payload.data[0].embedding


@lru_cache(maxsize=1)
def get_graph_driver() -> GraphDriver:
    settings = get_settings()
    return cast(
        GraphDriver,
        cast(
            object,
            GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value()),
            ),
        ),
    )


@lru_cache(maxsize=1)
def get_vllm_client() -> VllmClient:
    settings = get_settings()
    return VllmClient(
        settings.vllm_url,
        settings.embedding_url,
        settings.model_name,
        settings.embedding_model,
    )
