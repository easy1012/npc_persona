# DB CONTROL KNOWLEDGE BASE

## OVERVIEW

Direct Neo4j source importer area. This path reads `rsc/data` Markdown/YAML and creates the live graph used by GraphRAG retrieval.

## STRUCTURE

```text
src/db_control/
|-- import_story_source_to_neo4j.py    # current source-data importer
`-- insert_neo.py                      # older/simple insertion helper
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Validate source parsing without DB | `import_story_source_to_neo4j.py` | Run with `--dry-run`. |
| Change source-to-graph mapping | `import_story_source_to_neo4j.py` | Handles NPC, Quest, Role, Event, Clue, Truth, Location, `KnowledgeChunk`. |
| Write import report | `import_story_source_to_neo4j.py` | Default report path is `output/reports/neo4j_story_source_import_report.md`. |
| Legacy insertion reference | `insert_neo.py` | Do not extend unless the task is explicitly about this helper. |

## CONVENTIONS

- Prefer `uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j` before any live import.
- Live import uses environment-backed Neo4j settings: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`.
- Use merge-style imports for normal operation; `--reset` is destructive and needs explicit user approval.
- Keep the importer aligned with canonical `rsc/data` schema, not generated `output/` files.
- Preserve `KnowledgeChunk` creation from NPC story chunks because Streamlit retrieval depends on it.

## ANTI-PATTERNS

- Do not commit credentials or default real passwords in new files.
- Do not run DB reset commands as a verification shortcut.
- Do not silently change graph labels or relationship names without updating docs and retrieval code.
- Do not use generated pipeline CSVs as the source for this importer path.

## QUICK CHECKS

```bash
uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j
```
