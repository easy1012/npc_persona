# Database Server

This folder is the deployment root for the storage server. Set `DATABASE_BIND_IP` to the server's private address. Firewall ports `5432` and `7687` so only the model server private address can connect.

```bash
cp .env.example .env
docker compose --env-file .env config
docker compose --env-file .env up -d
docker compose --env-file .env --profile tools run --rm migrate
```

PostgreSQL stores the full document corpus, vector embeddings, accounts, saves, messages, and quest progress. Neo4j stores the immediately required NPC, quest, clue, truth, global-story relationships, and gated `KnowledgeChunk` nodes. Never run a Neo4j reset or remove database volumes without explicit approval.

Run the migrations owned by this folder from the checked-out repository root after PostgreSQL is healthy:

```bash
uv run --frozen alembic -c alembic.ini upgrade head
POSTGRES_DSN=postgresql+psycopg://hazel:secret@127.0.0.1:5432/hazel uv run --frozen python scripts/ingest_full_corpus.py
```

Back up PostgreSQL and Neo4j independently to storage outside this physical server.

Canonical data validation and Neo4j loading paths:

Set `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, and `NEO4J_DATABASE` in `.env` before live loading.

```bash
python scripts/story_pipeline/run_pipeline.py
python scripts/story_pipeline/run_pipeline.py --load-neo4j
python scripts/story_pipeline/load_neo4j.py
python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data
```

The default pipeline does not reset Neo4j. A reset remains destructive and requires explicit approval.
The destructive helper is `scripts/story_pipeline/reset_neo4j_dev.py`; do not run it during normal loading.
