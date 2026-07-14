# 설계 검증 Docker 기록

이 문서는 역사 기록이다. 현재 root에 `compose.design-test.yaml`이 없으면 아래 예전 명령을 current command로 실행하지 않는다.

## 현재 안내

현재 배포와 검증은 split 문서를 따른다.

1. 모델 서버 실행은 [deployment.md](deployment.md)를 따른다.
2. 데이터 서버 실행, migration, PostgreSQL full corpus ingest, Neo4j import는 [../../database-server/docs/README.md](../../database-server/docs/README.md)를 따른다.
3. 현재 `model-server/compose.yaml` 서비스는 `proxy`, `api`, `streamlit`, optional GPU profile `vllm`이다.
4. 현재 `database-server/compose.yaml` 서비스는 `postgres`, `neo4j`, tools profile `migrate`다.

## 역사적 배경

예전 Version 2 설계 검증에서는 Windows Docker Desktop에서 별도 Compose project, 별도 host port, 별도 Neo4j volume을 쓰는 `compose.design-test.yaml` 스택을 사용했다. 그 스택은 발표 캡처와 monolith 시대 검증을 위한 임시 구성이다.

당시 의도는 다음과 같았다.

```text
기본 개발 stack
  Streamlit, Neo4j, vLLM을 한 Compose 경계에서 검증

설계 검증 stack
  host port와 volume을 바꿔 기존 개발 container와 충돌 방지
```

현재 production split에서는 이 방식이 기준이 아니다. Neo4j는 model server Compose에 없고, Streamlit은 FastAPI만 호출한다.

## 보존하는 주의점

1. real token과 real password를 문서에 쓰지 않는다.
2. Neo4j reset은 전체 graph를 지울 수 있으므로 명시 승인 없이 실행하지 않는다.
3. Docker volume 삭제는 persistent data를 지우는 destructive 작업이다.
4. 발표용 port, capture URL, local model override는 현재 운영 기본값이 아니다.

## 예전 명령을 읽는 방법

과거 로그나 발표 자료에서 다음 형태를 보더라도 현재 실행 절차로 복사하지 않는다.

```text
docker compose --env-file .env.design-test -f compose.design-test.yaml ...
```

필요하면 먼저 해당 파일이 실제로 존재하는지 확인하고, 목적이 역사 재현인지 current deployment인지 분리한다. current deployment는 [deployment.md](deployment.md)와 [../../database-server/docs/README.md](../../database-server/docs/README.md)가 기준이다.
