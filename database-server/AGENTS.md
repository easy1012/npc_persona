# Database Server

This repository owns canonical story data, PostgreSQL/pgvector migrations, Neo4j import tooling, persistent storage Compose resources, and database-node Kubernetes manifests.

- Never reset Neo4j, delete volumes, or remove persistent data without explicit approval.
- Run `uv sync --frozen`, `uv run --frozen python scripts/story_pipeline/validate_data.py`, and the importer with `--dry-run` before live imports.
- The model server connects only through the private PostgreSQL and Neo4j addresses.
- `rsc/data` is canonical; `output` is generated.
