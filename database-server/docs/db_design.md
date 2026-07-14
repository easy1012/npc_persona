# 데이터 서버 DB 설계

이 문서는 현재 split 배포 기준의 canonical storage 설계다. FastAPI가 유일한 production DB boundary이며, Streamlit은 FastAPI만 호출한다.

## 1. 현재 storage topology

```text
model-server FastAPI
  -> PostgreSQL + pgvector
  -> Neo4j
  -> optional vLLM

database-server
  postgres  pgvector/pgvector:pg16
  neo4j     neo4j:5
  migrate   tools profile
```

`database-server/compose.yaml`은 PostgreSQL 5432와 Neo4j 7687을 `DATABASE_BIND_IP`에 bind한다. public Internet에 직접 공개하지 않는다.

## 2. PostgreSQL runtime schema

Alembic migration은 runtime state와 full corpus를 PostgreSQL에 둔다.

| Table | Owner role |
| --- | --- |
| `players` | guest 또는 account player root |
| `accounts` | email, password hash, admin flag |
| `browser_sessions` | opaque token hash, expiry, revocation |
| `saves` | player save slot과 current selection |
| `conversations` | save 안의 NPC별 durable thread |
| `turn_attempts` | idempotency key, `llm_pending`, `succeeded`, `failed` state |
| `messages` | ordered user와 assistant messages |
| `quest_progress` | save별 quest state와 allowed hint level |
| `observed_clues` | save와 quest 안에서 관찰한 clue |
| `npc_memory_summaries` | NPC별 compact prompt memory |
| `admin_audit_events` | admin mutation audit trail |
| `full_knowledge_documents` | full corpus document, metadata, pgvector embedding |

`full_knowledge_documents.embedding`은 nullable pgvector `Vector(768)`이다. `scripts/ingest_full_corpus.py`는 `CORPUS_SOURCE_DIR` 기본값 `rsc/data` 아래 Markdown, YAML, JSON을 읽어 `source_id`, `source_type`, `title`, `content`, metadata를 upsert하지만 embedding을 생성하지는 않는다. Vector retrieval을 사용하려면 embedding을 별도 적재해야 하며, 현재 FastAPI는 solved 상태에서 lexical fallback도 사용한다.

## 3. Neo4j graph ownership

Neo4j는 canonical story graph와 reveal policy graph를 맡는다.

| Label | Unique key | 역할 |
| --- | --- | --- |
| `NPC` | `npc_id` | NPC profile, role, location, quest 참여 |
| `Role` | `role_id` | player와 NPC 역할 |
| `Location` | `location_id` | 마을 장소와 분위기 |
| `Quest` | `quest_id` | quest state와 주요 연결의 기준 |
| `Event` | `event_id` | story event |
| `Clue` | `clue_id` | 관찰 단서 |
| `Truth` | `truth_id` | 정답 또는 reveal 대상 진실 |
| `KnowledgeChunk` | `chunk_id` | NPC가 말할 수 있는 graph scoped 근거 지식 |

주요 relationship은 다음과 같다.

| Relationship | From to To | 의미 |
| --- | --- | --- |
| `HAS_ROLE` | `NPC` to `Role` | NPC 역할 |
| `LOCATED_AT` | `NPC` to `Location` | NPC 기본 위치 |
| `PARTICIPATES_IN` | `NPC` to `Quest` | 대표 quest 참여 |
| `STARTS_AT` | `Quest` to `Location` | quest 시작 위치 |
| `INVOLVES` | `Quest` to `NPC` | quest 관련 NPC |
| `REQUIRES_CLUE` | `Quest` to `Clue` | 풀이에 필요한 clue |
| `HAS_ANSWER` | `Quest` to `Truth` | quest answer truth |
| `OCCURRED_AT` | `Event` to `Location` | event 발생 장소 |
| `CAUSED_BY` | `Event` to `Truth` | event 원인 |
| `FOUND_AT` | `Clue` to `Location` | clue 발견 장소 |
| `POINTS_TO` | `Clue` to `Truth` | clue가 가리키는 truth |
| `KNOWS` | `NPC` to `KnowledgeChunk` | NPC가 말할 수 있는 지식 |
| `RELATED_TO` | `KnowledgeChunk` to `Quest` | chunk 관련 quest |
| `MENTIONS` | `KnowledgeChunk` to `Location` | chunk가 언급한 location |
| `ABOUT` | `KnowledgeChunk` to `Event` | chunk가 다루는 event |
| `POINTS_TO` | `KnowledgeChunk` to `Clue` | chunk가 제공하는 clue |

`POINTS_TO`는 label 조합으로 의미가 구분된다.

## 4. Canonical source mapping

`rsc/data`가 canonical source다.

```text
rsc/data/npcs/*.md         -> NPC, KnowledgeChunk
rsc/data/locations/*.md    -> Location
rsc/data/quests/*.yaml     -> Quest
rsc/data/world/roles.yaml  -> Role
rsc/data/world/events.yaml -> Event
rsc/data/world/clues.yaml  -> Clue
rsc/data/world/truths.yaml -> Truth
```

`output/`은 generated artifact다. import report, integrated JSON/YAML, Neo4j CSV를 보관할 수 있지만 원천으로 편집하지 않는다.

## 5. FastAPI retrieval boundary

FastAPI는 turn completion 때 storage를 다음 순서로 사용한다.

1. PostgreSQL session과 save를 확인한다.
2. Conversation과 user message, turn attempt를 PostgreSQL에 저장한다.
3. Neo4j에서 `npc_id`, `quest_id`, player role, quest state, allowed hint level, answer reveal 조건으로 `KnowledgeChunk`를 조회한다.
4. Answer reveal이 허용되고 quest state가 `solved`일 때만 PostgreSQL `full_knowledge_documents`를 pgvector와 lexical fallback으로 조회한다.
5. Prompt를 만든 뒤 vLLM 응답을 받아 assistant message와 turn status를 PostgreSQL에 저장한다.

이 경계 때문에 PostgreSQL full corpus는 정답 공개 허용 전 prompt에 들어가지 않는다.

## 6. Import와 migration 명령

Root uv workspace는 하나의 `.venv`를 쓴다. member 문서의 명령도 `uv run --frozen`을 기본으로 쓴다.

```bash
uv run --frozen alembic -c alembic.ini upgrade head
# POSTGRES_DSN을 현재 shell에 먼저 설정한다.
uv run --frozen python scripts/ingest_full_corpus.py
uv run --frozen python scripts/story_pipeline/validate_data.py
uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j
```

Live import는 dry run이 통과한 뒤 실행한다.

```bash
uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --database neo4j
```

## 7. Destructive 작업 경고

`--reset`은 Neo4j graph 전체를 삭제한 뒤 다시 적재할 수 있다. Production 또는 shared database에서 명시 승인 없이 쓰지 않는다.

Docker volume 삭제는 PostgreSQL과 Neo4j persistent data를 지운다. 명시 승인 없이는 실행하지 않는다.

## 8. 검증 증거

2026-07-14 evidence는 database tests 36 PASS다. 관련 model tests 124 plus 2 PASS와 live quest quality matrix 14 of 14 PASS도 split 통합 상태의 참고 증거다. 이 숫자는 특정 시점의 evidence이며 영구 invariant가 아니다.

## 9. 관련 문서

1. [README.md](README.md), database docs map.
2. [neo4j_story_import_guide.md](neo4j_story_import_guide.md), Neo4j import.
3. [../../model-server/docs/system_architecture.md](../../model-server/docs/system_architecture.md), current runtime architecture.
