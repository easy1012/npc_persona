# 데이터 서버 문서 지도

이 디렉터리는 현재 `database-server`의 storage, migration, canonical data, import, augmentation, safety 문서를 안내한다. `database-server`는 PostgreSQL, pgvector, Neo4j, migration, canonical `rsc/data`를 소유한다. `model-server`는 FastAPI, Streamlit, proxy, optional vLLM을 소유한다.

FastAPI가 유일한 production DB boundary다. Streamlit이나 player browser가 PostgreSQL 또는 Neo4j에 직접 접근하는 경로는 현재 production 기준이 아니다.

## 현재 기준 문서

1. [db_design.md](db_design.md), PostgreSQL runtime schema, pgvector full corpus, Neo4j graph ownership, FastAPI boundary.
2. [neo4j_story_import_guide.md](neo4j_story_import_guide.md), canonical `rsc/data`를 Neo4j graph로 적재하는 방법과 safety note.
3. [MVP_NPC_EXPANSION_GUIDE.md](MVP_NPC_EXPANSION_GUIDE.md), NPC와 story data 확장 기록. runtime model 설명은 역사 맥락을 포함한다.
4. [NEO4J_GRAPH_STRUCTURE_VISUAL_GUIDE.md](NEO4J_GRAPH_STRUCTURE_VISUAL_GUIDE.md), Neo4j graph 구조 시각 설명.
5. [story_source_classification.md](story_source_classification.md), story source 분류 기준.
6. [DATA_AUGMENTATION_REPORT.md](DATA_AUGMENTATION_REPORT.md), data augmentation 기록과 검증 근거.
7. [data-augmentation-design.md](data-augmentation-design.md), augmentation 설계 기록.

## 데이터 소유권

PostgreSQL은 다음을 맡는다.

1. `players`, guest와 account player root.
2. `accounts`, account identity와 admin flag.
3. `browser_sessions`, opaque session token hash와 expiry.
4. `saves`, player save slot.
5. `conversations`, save와 NPC별 durable thread.
6. `turn_attempts`, idempotency key와 pending, succeeded, failed state.
7. `messages`, ordered user와 assistant message.
8. `quest_progress`, quest state와 allowed hint level.
9. `observed_clues`, save 안에서 본 clue.
10. `npc_memory_summaries`, prompt memory summary.
11. `admin_audit_events`, admin mutation audit.
12. `full_knowledge_documents`, full corpus text와 pgvector `Vector(768)` embedding.

Neo4j는 다음을 맡는다.

1. `NPC`, `Quest`, `Clue`, `Truth`, `Location`, `Event`, `KnowledgeChunk`.
2. NPC가 알고 있는 chunk 관계.
3. Quest, clue, truth, event, location 관계.
4. Answer reveal policy graph.
5. Graph scoped retrieval에 필요한 story relationship.

## Canonical source와 generated output

`rsc/data`가 canonical story source다. NPC, quest, world, location 원천을 바꿀 때는 여기만 수정한다. `output/`은 generated artifact이며 source of truth가 아니다.

## 기본 운영 순서

1. `.env`를 만들고 `DATABASE_BIND_IP`를 private address로 설정한다.
2. `docker compose --env-file .env config`로 Compose를 확인한다.
3. `docker compose --env-file .env up -d postgres neo4j`로 storage service를 시작한다.
4. `docker compose --env-file .env --profile tools run --rm migrate` 또는 `uv run --frozen alembic -c alembic.ini upgrade head`로 migration을 적용한다.
5. 현재 shell에 `POSTGRES_DSN`을 private PostgreSQL DSN으로 설정한 뒤 `uv run --frozen python scripts/ingest_full_corpus.py`로 full corpus를 PostgreSQL에 넣는다.
6. `uv run --frozen python scripts/story_pipeline/validate_data.py`로 source data를 검증한다.
7. `uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j`로 dry run을 수행한다.
8. dry run이 통과한 뒤 승인된 환경에서 live Neo4j import를 실행한다.

## Safety rules

1. 실제 비밀번호, token, session 값을 문서에 쓰지 않는다.
2. PostgreSQL과 Neo4j port는 public Internet에 직접 공개하지 않는다.
3. `DATABASE_BIND_IP`는 private address 또는 통제된 bind address로 둔다.
4. Neo4j `--reset`은 모든 graph node를 지울 수 있다. 명시 승인 없이는 실행하지 않는다.
5. Docker volume 삭제는 persistent data를 지운다. 명시 승인 없이는 실행하지 않는다.
6. Backups는 PostgreSQL과 Neo4j를 독립적으로 준비하고 restore 절차를 검증한다.

## Model server cross link

Application runtime, HTTPS proxy, Streamlit, FastAPI, optional vLLM 문서는 [../../model-server/docs/README.md](../../model-server/docs/README.md)를 기준으로 본다.
