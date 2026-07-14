# 헤이즐 NPC 서비스 인수인계 보고서

이 보고서는 현재 split 배포 기준의 인수인계 요약이다. 이전 `Streamlit + Neo4j` monolith 세부 설명은 `npc_persona_version_2/`와 발표 자료에 역사 기록으로 남아 있다.

## 1. 현재 목적

헤이즐 NPC 서비스는 플레이어의 현재 save, NPC, quest state, hint level, answer reveal 조건에 맞는 지식만 prompt에 넣어 NPC가 대답하게 만드는 GraphRAG 기반 게임 대화 서비스다.

현재 production 경계는 FastAPI다. Streamlit은 UI를 그리며 `GAME_API_URL=http://api:8000/api`로 FastAPI만 호출한다. FastAPI는 PostgreSQL, Neo4j, 선택 vLLM을 private network에서 사용한다.

## 2. 배포 루트

```text
model-server
  proxy       Caddy HTTPS 443
  api         FastAPI
  streamlit   player UI
  vllm        optional GPU profile

database-server
  postgres    PostgreSQL + pgvector
  neo4j       story graph
  migrate     tools profile migration helper
  rsc/data    canonical story source
```

`model-server/compose.yaml`에는 Neo4j나 PostgreSQL 서비스가 없다. `database-server/compose.yaml`은 `DATABASE_BIND_IP`로 PostgreSQL 5432와 Neo4j 7687을 private address에 bind한다.

## 3. 주요 사용자 흐름

1. 첫 방문에서 FastAPI가 session bootstrap을 처리하고 guest player, save, browser session을 만든다.
2. Streamlit은 NPC별 conversation과 game state를 FastAPI에서 읽는다.
3. 사용자가 turn을 보내면 Streamlit은 `Idempotency-Key`와 함께 FastAPI에 요청한다.
4. FastAPI는 user message와 turn attempt를 PostgreSQL에 저장한다.
5. FastAPI는 Neo4j graph chunk를 조회하고, answer reveal이 허용되고 quest state가 solved일 때만 PostgreSQL full corpus를 추가 조회한다.
6. FastAPI는 prompt를 만들고 vLLM을 호출한다.
7. assistant message와 turn status는 PostgreSQL에 확정된다. 현재 turn endpoint는 해당 quest progress가 없으면 `in_progress`, hint level 1로 초기화하지만, deterministic quest runtime과 NPC memory 자동 갱신을 아직 연결하지 않았다.
8. account conversion은 guest progress를 보존하며 session token을 회전한다.

## 4. 데이터 소유권

PostgreSQL은 mutable runtime state와 full corpus를 소유한다. 마이그레이션은 `players`, `accounts`, `browser_sessions`, `saves`, `conversations`, `turn_attempts`, `messages`, `quest_progress`, `observed_clues`, `npc_memory_summaries`, `admin_audit_events`, `full_knowledge_documents`를 만든다. `full_knowledge_documents.embedding`은 pgvector `Vector(768)`이다.

Neo4j는 `NPC`, `Quest`, `Clue`, `Truth`, `Location`, `Event`, `KnowledgeChunk`와 reveal policy graph를 소유한다.

`database-server/rsc/data`가 canonical story source다. `output/`은 generated artifact이며 원천으로 편집하지 않는다.

## 5. 기준 문서

1. 현재 모델 서버 아키텍처: [system_architecture.md](system_architecture.md)
2. 현재 모델 서버 배포: [deployment.md](deployment.md)
3. 현재 database 문서 지도: [../../database-server/docs/README.md](../../database-server/docs/README.md)
4. 현재 DB 설계: [../../database-server/docs/db_design.md](../../database-server/docs/db_design.md)
5. 현재 Neo4j import: [../../database-server/docs/neo4j_story_import_guide.md](../../database-server/docs/neo4j_story_import_guide.md)
6. Split 설계 출처: [plans/2026-07-11-npc-game-service-design.md](plans/2026-07-11-npc-game-service-design.md)

## 6. 검증 증거

2026-07-14 확인 evidence는 다음과 같다. 이 숫자는 특정 시점의 검증 기록이며 영구 invariant가 아니다.

1. model tests, 124 plus 2 PASS.
2. database tests, 36 PASS.
3. live quest quality matrix, 14 of 14 PASS.

새 배포나 변경 후에는 model tests, database tests, live quest path를 다시 확인하고 새 evidence를 남긴다.

## 7. 운영 주의점

1. 실제 비밀번호, token, session 값은 문서에 쓰지 않는다.
2. Streamlit이 DB에 직접 붙는다고 문서화하지 않는다.
3. Neo4j를 model server Compose 서비스로 문서화하지 않는다.
4. Neo4j reset, PostgreSQL wipe, Docker volume 삭제는 destructive 작업이며 명시 승인 없이는 실행하지 않는다.
5. `compose.design-test.yaml` 관련 예전 명령은 역사 기록이다. 현재 파일이 없으면 current command로 제시하지 않는다.
6. member 폴더 명령은 root uv workspace의 단일 `.venv`를 전제로 `uv run --frozen` 형태를 쓴다.

## 8. 역사 자료 읽는 법

`npc_persona_version_2/`, 발표 소스, 과거 QA 로그에는 당시 구현과 검증 맥락이 있다. 그 안의 Streamlit direct Neo4j 접근, monolith Compose, design test stack 설명은 current deployment가 아니라 learning과 history로 읽는다.
