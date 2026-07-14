# 헤이즐 NPC 서비스 현재 아키텍처

이 문서는 현재 split 배포 기준의 구조만 설명한다. 오래된 `Streamlit + Neo4j` 단일 Compose 설명과 발표용 구성은 역사 자료로 남아 있으며, 현재 production 경계로 읽지 않는다.

## 1. 배포 경계

현재 저장소는 두 배포 루트를 가진다.

```text
model-server
  proxy       HTTPS 443 공개 Caddy
  api         FastAPI, 유일한 production DB 경계
  streamlit   플레이어 UI, GAME_API_URL=http://api:8000/api
  vllm        GPU profile에서만 실행하는 선택 추론 서비스

database-server
  postgres    PostgreSQL 16 + pgvector
  neo4j       story graph와 reveal policy graph
  migrate     tools profile에서만 실행하는 migration helper
```

`model-server/compose.yaml`에 Neo4j 서비스는 없다. `database-server/compose.yaml`의 PostgreSQL과 Neo4j port는 `DATABASE_BIND_IP`에 바인딩되며, 방화벽으로 model server private address만 허용해야 한다.

## 2. 런타임 호출 흐름

```text
플레이어 브라우저
  -> proxy HTTPS 443
  -> streamlit
  -> FastAPI http://api:8000/api
  -> PostgreSQL, Neo4j, 선택 vLLM
  -> FastAPI
  -> streamlit
  -> 플레이어 브라우저
```

Streamlit은 화면 상태와 입력 UI를 맡는다. 세션, 계정, 대화, 저장 슬롯, quest state, idempotency, retrieval, prompt completion은 FastAPI 경계를 지난다. 따라서 현재 production 문서에서 Streamlit이 PostgreSQL이나 Neo4j에 직접 접근한다고 쓰면 안 된다.

## 3. FastAPI route 책임

현재 FastAPI는 다음 사용자 흐름을 제공한다.

1. `POST /api/sessions/bootstrap`, 첫 방문 session bootstrap과 guest save 생성.
2. `POST /api/accounts/convert`, guest account conversion과 session token rotation.
3. `GET /api/game/npcs/{npc_id}/conversation`, save 안의 NPC별 durable conversation 조회.
4. `GET /api/game/state`, quest progress와 allowed hint level 조회.
5. `POST /api/game/turns`, `Idempotency-Key` 기반 turn 생성, 재시도, completion.

FastAPI는 PostgreSQL transaction을 짧게 유지한다. 사용자 message와 pending attempt를 먼저 저장하고, 외부 retrieval과 vLLM 호출 뒤 assistant message와 turn status를 별도 transaction으로 확정한다. 실패한 turn은 failed로 남고 같은 idempotency key로 다시 시도할 수 있다.

## 4. 데이터 소유권

PostgreSQL은 mutable runtime state와 full corpus를 맡는다.

1. `players`
2. `accounts`
3. `browser_sessions`
4. `saves`
5. `conversations`
6. `turn_attempts`
7. `messages`
8. `quest_progress`
9. `observed_clues`
10. `npc_memory_summaries`
11. `admin_audit_events`
12. `full_knowledge_documents`, `pgvector` `Vector(768)` embedding 포함

Neo4j는 story graph와 reveal policy를 맡는다.

1. `NPC`
2. `Quest`
3. `Clue`
4. `Truth`
5. `Location`
6. `Event`
7. `KnowledgeChunk`
8. 위 node 간 관계와 answer reveal policy graph

canonical story source는 `database-server/rsc/data`다. `database-server/output/`은 generated artifact이며 원천으로 편집하지 않는다.

## 5. Retrieval과 reveal 규칙

FastAPI는 turn completion 때 두 retrieval 경로를 합친다.

1. Neo4j에서 현재 `npc_id`, `quest_id`, player role, quest state, allowed hint level, answer reveal 조건을 통과한 graph scoped `KnowledgeChunk`를 조회한다.
2. PostgreSQL `full_knowledge_documents`는 answer reveal이 허용되고 quest state가 `solved`일 때만 pgvector와 lexical fallback으로 조회한다.
3. prompt에는 graph chunk를 먼저 넣고, 허용된 경우에만 full corpus document를 `마을 기록` chunk로 추가한다.

정답 민감 정보는 graph reveal 조건과 quest state가 열리기 전까지 prompt에 들어가지 않는다.

## 6. 배포 서비스 요약

`model-server` 서비스 책임은 다음과 같다.

1. `proxy`, public HTTPS 443, `api`와 `streamlit` health를 기다린다.
2. `api`, `POSTGRES_DSN`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, vLLM과 embedding endpoint를 환경변수로 받는다.
3. `streamlit`, `GAME_API_URL=http://api:8000/api`로 FastAPI만 호출한다.
4. `vllm`, `profiles: ["gpu"]`일 때만 시작하며 local model directory를 read only로 mount한다.

`database-server` 서비스 책임은 다음과 같다.

1. `postgres`, `pgvector/pgvector:pg16`, port `5432`를 `DATABASE_BIND_IP`에 bind.
2. `neo4j`, Neo4j 5, Bolt `7687`을 `DATABASE_BIND_IP`에 bind.
3. `migrate`, `profiles: ["tools"]`에서 Alembic migration 실행 보조.

## 7. 검증 증거 읽는 법

2026-07-14 검증 기록은 당시 상태의 evidence다. 영구 invariant가 아니다.

1. model side test receipt, 124 tests plus 2 tests PASS.
2. database side test receipt, 36 tests PASS.
3. live quest quality matrix, 14 of 14 PASS.

새 변경을 판단할 때는 이 숫자를 고정 약속으로 쓰지 말고, 같은 성격의 regression evidence를 다시 남긴다.

## 8. 관련 문서

1. [deployment.md](deployment.md), 현재 실행 절차.
2. [PROJECT_HANDOFF_REPORT.md](PROJECT_HANDOFF_REPORT.md), 인수인계 요약.
3. [../../database-server/docs/README.md](../../database-server/docs/README.md), database canonical 문서 지도.
4. [../../database-server/docs/db_design.md](../../database-server/docs/db_design.md), PostgreSQL과 Neo4j storage 설계.
5. [plans/2026-07-11-npc-game-service-design.md](plans/2026-07-11-npc-game-service-design.md), split 설계 출처.
