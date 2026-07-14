# 모델 서버 문서 지도

이 디렉터리는 현재 `model-server`의 애플리케이션, 모델, 런타임 문서를 안내한다. 저장소는 지금 두 배포 루트로 나뉜다. `model-server`는 프록시, FastAPI, Streamlit, 선택 실행 vLLM을 맡고, `database-server`는 PostgreSQL, pgvector, Neo4j, 마이그레이션, canonical `rsc/data`를 맡는다.

현재 운영 경계는 FastAPI다. Streamlit은 `GAME_API_URL=http://api:8000/api`로 FastAPI만 호출한다. Streamlit이 PostgreSQL이나 Neo4j에 직접 붙는 구조는 현재 production 경로가 아니다.

## 현재 운영 기준 문서

1. [system_architecture.md](system_architecture.md), 현재 split topology, FastAPI 경계, retrieval 흐름.
2. [deployment.md](deployment.md), GPU 서버 배포, HTTPS 프록시, API, Streamlit, 선택 vLLM 실행.
3. [PROJECT_HANDOFF_REPORT.md](PROJECT_HANDOFF_REPORT.md), 현재 인수인계 요약, 검증 증거, 남은 주의점.

## 설계, 학습, 역사 문서

1. [plans/2026-07-11-npc-game-service-design.md](plans/2026-07-11-npc-game-service-design.md), 현재 split 설계의 출처가 된 승인 계획.
2. [.study/README.md](.study/README.md), 학습 문서 지도. 장별 monolith 설명은 학습과 역사로 읽는다.
3. [design_test_docker.md](design_test_docker.md), 예전 설계 검증 스택 기록.
4. [quest_auto_progression_plan.md](quest_auto_progression_plan.md), superseded된 초기 quest 자동 진행 계획.

## 애플리케이션 범위

1. `proxy`는 Caddy이며 HTTPS 443을 공개한다.
2. `api`는 FastAPI이며 세션 bootstrap, account conversion, NPC별 conversation, game state, idempotent turn 처리를 제공한다.
3. `streamlit`은 플레이어 UI이며 FastAPI만 호출한다.
4. `vllm`은 GPU profile로만 켜지는 선택 서비스다.
5. FastAPI는 Neo4j의 graph scoped chunk와 PostgreSQL의 full corpus retrieval을 합친다. pgvector full document는 answer reveal이 허용되고 quest state가 solved일 때만 쓴다.

현재 turn endpoint는 quest progress가 없을 때 `in_progress`, hint level 1로 초기화한다. `src/streamlit`의 deterministic quest runtime과 NPC memory 자동 갱신은 아직 FastAPI turn 경로에 연결되지 않았다.

## 데이터 서버 canonical 문서

다음 주제는 `database-server`가 canonical이다. model 쪽 파일은 이전 링크를 깨지 않기 위한 redirect stub이다.

1. [db_design.md](db_design.md) -> [../../database-server/docs/db_design.md](../../database-server/docs/db_design.md)
2. [neo4j_story_import_guide.md](neo4j_story_import_guide.md) -> [../../database-server/docs/neo4j_story_import_guide.md](../../database-server/docs/neo4j_story_import_guide.md)
3. [NEO4J_GRAPH_STRUCTURE_VISUAL_GUIDE.md](NEO4J_GRAPH_STRUCTURE_VISUAL_GUIDE.md) -> [../../database-server/docs/NEO4J_GRAPH_STRUCTURE_VISUAL_GUIDE.md](../../database-server/docs/NEO4J_GRAPH_STRUCTURE_VISUAL_GUIDE.md)
4. [story_source_classification.md](story_source_classification.md) -> [../../database-server/docs/story_source_classification.md](../../database-server/docs/story_source_classification.md)
5. [DATA_AUGMENTATION_REPORT.md](DATA_AUGMENTATION_REPORT.md) -> [../../database-server/docs/DATA_AUGMENTATION_REPORT.md](../../database-server/docs/DATA_AUGMENTATION_REPORT.md)
6. [MVP_NPC_EXPANSION_GUIDE.md](MVP_NPC_EXPANSION_GUIDE.md) -> [../../database-server/docs/MVP_NPC_EXPANSION_GUIDE.md](../../database-server/docs/MVP_NPC_EXPANSION_GUIDE.md)

## 역사와 발표 자료

1. `presentation/`, `presentation_/`, `npc_persona_version_2/presentation_source/`는 발표 소스와 자산이다. 현재 배포 절차의 기준이 아니다.
2. `npc_persona_version_2/` 아래 보고서와 로그는 당시 검증 기록이다. 현재 split baseline과 다르면 역사 자료로 읽는다.
3. `legacy-root-README.md`는 이전 루트 README 보존본이다. 현재 실행은 [deployment.md](deployment.md)를 따른다.

## 명령 표기 원칙

루트 uv workspace는 하나의 `.venv`를 쓴다. 문서에 새 명령을 추가할 때는 member 폴더에서도 `uv run --frozen` 형태를 기본으로 쓴다. 실제 비밀번호나 토큰 예시는 쓰지 않는다.
