# 모델 서버 배포 가이드

이 문서는 현재 `model-server` 배포만 다룬다. PostgreSQL, pgvector, Neo4j, migration, canonical `rsc/data` 적재는 [../../database-server/docs/README.md](../../database-server/docs/README.md)를 따른다.

## 1. 전제

1. `database-server`가 먼저 배포되어 PostgreSQL과 Neo4j가 private network에서 접근 가능해야 한다.
2. PostgreSQL migration이 적용되어야 한다.
3. `database-server/rsc/data` 기준의 Neo4j graph와 PostgreSQL full corpus ingest가 끝나야 한다.
4. `model-server`의 public entry는 Caddy `proxy`의 HTTPS 443이다.
5. database port와 vLLM port는 public Internet에 직접 공개하지 않는다.

## 2. 환경 파일

`model-server`에서 환경 파일을 만든다.

```bash
cp .env.example .env
```

`.env`에는 실제 비밀번호와 token을 넣되 문서나 git에 쓰지 않는다. 필수 연결 값은 다음 성격이다.

```text
PUBLIC_HOSTNAME=<public-hostname>
POSTGRES_DSN=<private-postgres-dsn>
NEO4J_URI=<private-neo4j-bolt-uri>
NEO4J_USER=<neo4j-user>
NEO4J_PASSWORD=<neo4j-password>
MODEL_NAME=google/gemma-4-E4B-it
LOCAL_MODEL_DIR=<local-model-dir-for-gpu-profile>
```

Streamlit container에는 Compose가 `GAME_API_URL=http://api:8000/api`를 주입한다. 이 값은 production 경로에서 Streamlit이 FastAPI만 호출한다는 계약이다.

## 3. 설정 확인

```bash
docker compose --env-file .env config
```

이 명령은 파일 검증만 수행한다. 서비스 시작 전 `proxy`, `api`, `streamlit`, 선택 `vllm`만 model server에 있는지 확인한다. Neo4j나 PostgreSQL 서비스가 model Compose에 나오면 현재 split 기준과 맞지 않는다.

## 4. API와 Streamlit 시작

```bash
docker compose --env-file .env up -d api streamlit proxy
```

`proxy`는 `api`와 `streamlit` healthcheck를 기다린 뒤 HTTPS 443을 제공한다. `api`는 `/api/health`로 healthcheck를 받고, `streamlit`은 `/_stcore/health`로 healthcheck를 받는다.

## 5. 선택 vLLM 시작

GPU 서버에서 local model directory와 권한을 확인한 뒤에만 vLLM profile을 켠다.

```bash
docker compose --env-file .env --profile gpu up -d vllm
```

전체를 한 번에 올릴 때는 다음처럼 실행할 수 있다.

```bash
docker compose --env-file .env --profile gpu up -d api streamlit proxy vllm
```

vLLM은 OpenAI compatible chat completion과 embedding endpoint를 제공한다. 현재 Compose는 API의 `VLLM_URL`을 내부 `vllm` 서비스로 고정하고 `EMBEDDING_URL`과 `MODEL_NAME`만 환경변수로 받는다. 외부 추론 서비스를 쓰려면 현재 Compose 계약을 별도로 변경해야 하므로, 환경변수만 바꿔서 지원된다고 가정하지 않는다.

## 6. 현재 API 기능 확인

FastAPI가 제공해야 하는 사용자 흐름은 다음과 같다.

1. Session bootstrap.
2. Account conversion.
3. NPC별 conversation 조회.
4. Game state 조회.
5. `Idempotency-Key`가 있는 turn 생성과 재시도.

간단한 live check는 proxy 뒤 HTTPS endpoint 또는 private API endpoint에서 수행한다. cookie가 필요한 route는 browser나 API client로 확인한다.

## 7. database 작업 위치

다음 작업은 model server에서 실행하지 않는다.

1. Alembic migration.
2. PostgreSQL full corpus ingest.
3. Neo4j source import.
4. Neo4j reset.
5. database volume 삭제.

위 작업은 [../../database-server/docs/README.md](../../database-server/docs/README.md)와 [../../database-server/docs/db_design.md](../../database-server/docs/db_design.md)를 따른다. Neo4j reset과 volume 삭제는 destructive 작업이며 명시 승인 없이는 실행하지 않는다.

## 8. 검증 증거

2026-07-14 확인 evidence는 model 124 plus 2 PASS, database 36 PASS, live quest quality matrix 14 of 14 PASS다. 이 수치는 해당 시점의 검증 기록으로 남긴다. 새 배포나 변경 후에는 같은 범위의 테스트와 live path 확인을 다시 수행한다.

## 9. legacy 설계 검증 스택

이전 문서에는 root `compose.design-test.yaml`을 쓰는 Windows 검증 스택이 있었다. 현재 root에 그 파일이 없는 상태라면 current command로 실행하지 않는다. 자세한 배경은 [design_test_docker.md](design_test_docker.md)를 역사 기록으로 읽고, 현재 실행은 이 문서와 database server 문서를 따른다.
