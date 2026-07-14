# STORY DATA KNOWLEDGE BASE

## OVERVIEW

Canonical Hazel Village story source. Changes here drive both the offline pipeline and the direct Neo4j source importer.

## STRUCTURE

```text
rsc/data/
|-- npcs/         # NPC profile Markdown plus story chunks
|-- quests/       # quest YAML plus story_expansion
|-- locations/    # location Markdown
|-- world/        # roles, events, clues, truths, dialogue policies
`-- *.md          # broader chronicles/map reference material
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| NPC identity and known chunks | `npcs/*.md` | Frontmatter plus chunk body feeds `KnowledgeChunk`. |
| Quest requirements and answers | `quests/*.yaml` | Includes required/optional clues, truths, NPCs, locations, expansion. |
| World-level clue/truth IDs | `world/clues.yaml`, `world/truths.yaml` | Referenced by quests, NPCs, dialogues, validation. |
| Role and event vocabulary | `world/roles.yaml`, `world/events.yaml` | Keep IDs stable across generated outputs. |
| Location source text | `locations/*.md` | Used by importer and pipeline mapping. |

## CONVENTIONS

- Treat this directory as source of truth; `output/` is only a derived product.
- Keep IDs stable and descriptive. Quest, clue, truth, NPC, role, event, and location IDs are cross-file contracts.
- Put quest expansion material in each quest file's `story_expansion` field.
- NPC files are the right place for retrieval-oriented story chunks.
- The current dataset is small by design: 4 NPCs, 5 quests, 30 `KnowledgeChunk`s in dry-run output.

## ANTI-PATTERNS

- Do not rename IDs without updating every reference and rerunning validation.
- Do not place canonical story changes in `output/`.
- Do not make NPC text reveal forbidden truth titles or IDs.
- Do not add data that requires network/model access to validate basic consistency.

## QUICK CHECKS

```bash
uv run --frozen python scripts/story_pipeline/run_pipeline.py
uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j
```
