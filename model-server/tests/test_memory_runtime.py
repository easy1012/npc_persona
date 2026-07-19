from __future__ import annotations

import os
import unittest
from uuid import UUID

import psycopg

TEST_POSTGRES_DSN = os.environ.setdefault(
    "POSTGRES_DSN",
    "postgresql+asyncpg://hazel_test:hazel_test@127.0.0.1:55433/hazel_test",
)
TEST_SYNC_POSTGRES_DSN = TEST_POSTGRES_DSN.replace("postgresql+asyncpg://", "postgresql://")
os.environ.setdefault("NEO4J_URI", "bolt://unused:7687")
os.environ.setdefault("NEO4J_USER", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "unused")
os.environ.setdefault("VLLM_URL", "http://unused/v1/chat/completions")
os.environ.setdefault("MODEL_NAME", "fake")

from fastapi.testclient import TestClient  # noqa: E402

from src.game_service.clients import get_graph_driver, get_vllm_client  # noqa: E402
from src.game_service.db import get_session_factory  # noqa: E402
from src.game_service.main import app  # noqa: E402


class FakeRecord:
    def data(self) -> dict[str, object]:
        return {"chunk_id": "test", "title": "테스트 단서", "text": "확인된 마을 기록"}


class FakeGraph:
    def execute_query(
        self,
        query: str,
        **parameters: str | int | bool | None,
    ) -> tuple[list[FakeRecord], object, object]:
        _ = query, parameters
        return [FakeRecord()], object(), object()


class FakeLlm:
    async def embed(self, text: str) -> list[float]:
        _ = text
        return [0.0] * 768

    async def complete(self, prompt: str) -> str:
        if "<npc-memory-summary>" in prompt:
            return "플레이어는 마을 기록에 관해 두 차례 질문했다."
        if "확인된 마을 기록" not in prompt:
            raise AssertionError("hybrid graph context was not included")
        return "마을 기록을 확인했어요."


class SummaryFailingLlm(FakeLlm):
    async def complete(self, prompt: str) -> str:
        if "<npc-memory-summary>" in prompt:
            raise RuntimeError("summary unavailable")
        return await super().complete(prompt)


class MemoryRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app.dependency_overrides[get_graph_driver] = lambda: FakeGraph()
        app.dependency_overrides[get_vllm_client] = lambda: FakeLlm()

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.clear()

    def setUp(self) -> None:
        get_session_factory.cache_clear()

    def test_memory_compaction_persists_after_browser_state_reset(self) -> None:
        with TestClient(app, base_url="https://testserver") as browser:
            bootstrap = browser.post("/api/sessions/bootstrap")
            save_id = UUID(bootstrap.json()["save_id"])
            session_token = browser.cookies.get("hazel_session")
            with psycopg.connect(TEST_SYNC_POSTGRES_DSN) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO npc_memory_summaries
                            (id, save_id, npc_id, summary, recent_turn_count,
                             max_memory_count, summarized_through_ordinal)
                        VALUES (gen_random_uuid(), %s, %s, '', 0, 2, -1)
                        """,
                        (save_id, "mage_lumi"),
                    )
            payload = {"npc_id": "mage_lumi", "quest_id": "q_main", "content": "첫 질문"}
            first = browser.post("/api/game/turns", json=payload, headers={"Idempotency-Key": "memory-1"})
            second = browser.post(
                "/api/game/turns",
                json={**payload, "content": "두 번째 질문"},
                headers={"Idempotency-Key": "memory-2"},
            )
            self.assertEqual("succeeded", first.json()["status"])
            self.assertEqual("succeeded", second.json()["status"])
            with psycopg.connect(TEST_SYNC_POSTGRES_DSN) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT summary, summarized_through_ordinal, recent_turn_count
                        FROM npc_memory_summaries
                        WHERE save_id = %s AND npc_id = %s
                        """,
                        (save_id, "mage_lumi"),
                    )
                    checkpoint = cursor.fetchone()
            self.assertEqual(("플레이어는 마을 기록에 관해 두 차례 질문했다.", 1, 2), checkpoint)
            assert session_token is not None
            browser.cookies.clear()
            restored = browser.get(
                "/api/game/npcs/mage_lumi/conversation",
                headers={"Cookie": f"hazel_session={session_token}"},
            )
            self.assertEqual(4, len(restored.json()["messages"]))

    def test_summary_failure_does_not_fail_completed_turn(self) -> None:
        app.dependency_overrides[get_vllm_client] = lambda: SummaryFailingLlm()
        try:
            with TestClient(app, base_url="https://testserver") as browser:
                bootstrap = browser.post("/api/sessions/bootstrap")
                save_id = UUID(bootstrap.json()["save_id"])
                with psycopg.connect(TEST_SYNC_POSTGRES_DSN) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO npc_memory_summaries
                                (id, save_id, npc_id, summary, recent_turn_count,
                                 max_memory_count, summarized_through_ordinal)
                            VALUES (gen_random_uuid(), %s, %s, '', 0, 2, -1)
                            """,
                            (save_id, "patrol_leader_rio"),
                        )
                payload = {
                    "npc_id": "patrol_leader_rio",
                    "quest_id": "q_pig_escape",
                    "content": "흔적을 봤어",
                }
                _ = browser.post(
                    "/api/game/turns",
                    json=payload,
                    headers={"Idempotency-Key": "summary-failure-1"},
                )
                second = browser.post(
                    "/api/game/turns",
                    json={**payload, "content": "더 알려줘"},
                    headers={"Idempotency-Key": "summary-failure-2"},
                )
                self.assertEqual("succeeded", second.json()["status"])
                self.assertEqual(4, len(second.json()["conversation"]["messages"]))
        finally:
            app.dependency_overrides[get_vllm_client] = lambda: FakeLlm()
