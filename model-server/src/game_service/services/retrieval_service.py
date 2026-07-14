from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.game_service.models import FullKnowledgeDocument


class GraphDriver(Protocol):
    def execute_query(self, query: str, **parameters: str | int | bool | None) -> tuple[list[GraphRecord], object, object]: ...


class GraphRecord(Protocol):
    def data(self) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class HybridKnowledge:
    graph_chunks: tuple[dict[str, object], ...]
    full_documents: tuple[str, ...]


async def retrieve_hybrid_knowledge(
    db: AsyncSession,
    graph: GraphDriver,
    npc_id: str,
    quest_id: str,
    player_role: str,
    quest_state: str,
    allowed_hint_level: int,
    answer_reveal_allowed: bool,
    query_text: str,
    embedding: list[float],
) -> HybridKnowledge:
    graph_query = """
    MATCH (:NPC {npc_id: $npc_id})-[:KNOWS]->(k:KnowledgeChunk)
    WHERE (k.quest_id = $quest_id OR k.quest_id IS NULL)
      AND $player_role IN k.allowed_roles
      AND k.hint_level <= $allowed_hint_level
      AND (k.answer_sensitive = false OR ($answer_reveal_allowed = true AND $quest_state IN ['ready_to_answer', 'solved']))
    RETURN k.chunk_id AS chunk_id, k.title AS title, k.text AS text
    LIMIT 8
    """
    records, _, _ = graph.execute_query(
        graph_query,
        npc_id=npc_id,
        quest_id=quest_id,
        player_role=player_role,
        quest_state=quest_state,
        allowed_hint_level=allowed_hint_level,
        answer_reveal_allowed=answer_reveal_allowed,
    )
    graph_chunks = tuple(record.data() for record in records)
    if not answer_reveal_allowed or quest_state != "solved":
        return HybridKnowledge(graph_chunks, ())
    statement = (
        select(FullKnowledgeDocument.content)
        .where(FullKnowledgeDocument.embedding.is_not(None))
        .order_by(FullKnowledgeDocument.embedding.cosine_distance(embedding))
        .limit(8)
    )
    vector_documents = tuple((await db.scalars(statement)).all())
    remaining = 8 - len(vector_documents)
    lexical_documents: tuple[str, ...] = ()
    terms = tuple(word for word in query_text.split() if len(word) >= 2)[:5]
    if remaining > 0 and terms:
        lexical_statement = (
            select(FullKnowledgeDocument.content)
            .where(or_(*(FullKnowledgeDocument.content.ilike(f"%{term}%") for term in terms)))
            .order_by(FullKnowledgeDocument.source_id)
            .limit(remaining)
        )
        if vector_documents:
            lexical_statement = lexical_statement.where(
                FullKnowledgeDocument.content.not_in(vector_documents)
            )
        lexical_documents = tuple((await db.scalars(lexical_statement)).all())
    documents = vector_documents + lexical_documents
    return HybridKnowledge(graph_chunks, documents)
