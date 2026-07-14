from __future__ import annotations

import importlib.util
import io
from pathlib import Path
from typing import Protocol, cast
import unittest

from alembic.migration import MigrationContext
from alembic.operations import Operations
import yaml


ROOT = Path(__file__).resolve().parents[1]


class MigrationModule(Protocol):
    def upgrade(self) -> None:
        pass


def load_migration(path: Path) -> MigrationModule:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load migration: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(MigrationModule, cast(object, module))


def render_postgres_sql(*migration_paths: Path) -> str:
    buffer = io.StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql",
        opts={"as_sql": True, "output_buffer": buffer},
    )
    with Operations.context(context):
        for path in migration_paths:
            load_migration(path).upgrade()
    return buffer.getvalue()


class DatabaseDeploymentContractTest(unittest.TestCase):
    def test_runtime_state_migration_is_explicit_immutable_snapshot(self) -> None:
        source = (ROOT / "migrations" / "versions" / "0001_runtime_state.py").read_text(encoding="utf-8")
        expected_tables = {
            "accounts",
            "admin_audit_events",
            "browser_sessions",
            "conversations",
            "messages",
            "npc_memory_summaries",
            "observed_clues",
            "players",
            "quest_progress",
            "saves",
            "turn_attempts",
        }

        self.assertNotIn("from schema import", source)
        self.assertNotIn("Base.metadata", source)
        self.assertNotIn("create_all", source)
        self.assertNotIn("drop_all", source)
        self.assertNotIn("full_knowledge_documents", source)
        for table_name in expected_tables:
            self.assertIn(f'"{table_name}"', source)

    def test_runtime_and_full_knowledge_migrations_render_as_compatible_postgres_sql(self) -> None:
        sql = render_postgres_sql(
            ROOT / "migrations" / "versions" / "0001_runtime_state.py",
            ROOT / "migrations" / "versions" / "0002_full_knowledge_pgvector.py",
        )

        self.assertIn("CREATE TABLE players", sql)
        self.assertIn("FOREIGN KEY(player_id) REFERENCES players", sql)
        self.assertIn("UNIQUE (player_id, slot_index)", sql)
        self.assertIn("CREATE INDEX ix_messages_conversation_id", sql)
        self.assertIn("CREATE EXTENSION IF NOT EXISTS vector", sql)
        self.assertIn("CREATE TABLE full_knowledge_documents", sql)
        self.assertIn("CREATE INDEX ix_full_knowledge_source_type", sql)

    def test_compose_is_storage_only_and_private(self) -> None:
        compose = cast(dict[str, object], yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8")))
        services = cast(dict[str, dict[str, object]], compose["services"])
        self.assertEqual({"postgres", "neo4j", "migrate"}, set(services))
        self.assertIn("pgvector", str(services["postgres"]["image"]))
        self.assertEqual(["tools"], services["migrate"]["profiles"])
        neo4j_environment = cast(dict[str, str], services["neo4j"]["environment"])
        self.assertEqual({"NEO4J_AUTH"}, set(neo4j_environment))
        healthcheck = cast(dict[str, object], services["neo4j"]["healthcheck"])
        self.assertIn("NEO4J_AUTH", str(healthcheck["test"]))
        for name in ("postgres", "neo4j"):
            ports = cast(list[str], services[name]["ports"])
            self.assertTrue(all(port.startswith("${DATABASE_BIND_IP:") for port in ports))

    def test_migrations_own_pgvector_schema(self) -> None:
        source = (ROOT / "migrations" / "versions" / "0002_full_knowledge_pgvector.py").read_text(encoding="utf-8")
        self.assertIn("CREATE EXTENSION IF NOT EXISTS vector", source)
        self.assertIn("full_knowledge_documents", source)
        self.assertIn("Vector(768)", source)

    def test_kubernetes_storage_is_persistent_and_model_is_absent(self) -> None:
        source = (ROOT / "k8s" / "database-server.yaml").read_text(encoding="utf-8")
        self.assertIn("hazel-role: database", source)
        self.assertIn("kind: StatefulSet", source)
        self.assertIn("volumeClaimTemplates", source)
        self.assertNotIn("nvidia.com/gpu", source)


if __name__ == "__main__":
    _ = unittest.main()
