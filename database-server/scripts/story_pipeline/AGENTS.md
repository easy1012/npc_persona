# STORY PIPELINE KNOWLEDGE BASE

## OVERVIEW

Offline data-generation pipeline. It converts canonical `rsc/data` story sources into integrated YAML/JSON, Neo4j import CSV/Cypher, and validation reports under `output/`.

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Run the whole pipeline | `run_pipeline.py` | Build, validate, export, validate again; optional `--load-neo4j`. |
| Build integrated data | `build_integrated_data.py` | Largest file; central source-to-integrated transform. |
| Validate generated artifacts | `validate_data.py` | Checks JSON/YAML equality, IDs, forbidden truth leakage, CSV references. |
| Export Neo4j import files | `export_neo4j_import_files.py` | Writes `nodes_*.csv`, `relationships.csv`, schema/Cypher files. |
| Load generated CSVs | `load_neo4j.py` | Separate from direct source importer in `src/db_control`. |
| Reset dev Neo4j | `reset_neo4j_dev.py` | Destructive; use only with explicit approval. |

## CONVENTIONS

- `output/` is generated and ignored; regenerate it instead of hand-editing.
- Pipeline order is fixed: build integrated data, validate, export Neo4j files, validate again.
- Integrated JSON and YAML must match exactly.
- `relationships.csv` uses columns `start_label`, `start_id`, `relationship_type`, `end_label`, `end_id`, `properties_json`.
- CSV relationship validation only runs when `output/neo4j_import/relationships.csv` exists.
- Keep `story_expansion` in `rsc/data/quests/*.yaml`; do not create a separate source expansion tree.

## ANTI-PATTERNS

- Do not edit files under `output/integrated` or `output/neo4j_import` as canonical content.
- Do not weaken forbidden-truth validation to make generated dialogue pass.
- Do not bundle live Neo4j loading into default pipeline runs.
- Do not reset Neo4j from this directory without explicit approval.

## QUICK CHECKS

```bash
uv run --frozen python scripts/story_pipeline/run_pipeline.py
uv run --frozen python scripts/story_pipeline/validate_data.py
```
