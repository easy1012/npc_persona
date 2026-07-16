# 헤이즐 마을 웹 프론트엔드 전환 및 런타임 안정화 설계

## 목표

공개 플레이어 화면을 Streamlit에서 일반 웹 프론트엔드로 전환하고 브라우저가 동일 출처의 FastAPI를 직접 호출하게 한다. 기존의 마을 통신 수첩 UI/UX와 PostgreSQL·Neo4j·vLLM 경계는 유지하면서 다음 문제를 해결한다.

1. 대화 기반 퀘스트 진행과 단서 저장 누락
2. 브라우저 새로고침 후 게스트 세션 소실
3. 만료된 세션을 이용한 계정 전환
4. 메모리 압축 때문에 발생하는 턴 응답 시간 초과
5. 실패한 턴을 프론트엔드가 성공으로 처리하는 문제
6. 동일 대화에 대한 동시 턴의 질문·답변 순서 역전
7. async API 경로에서 동기 Neo4j 호출이 이벤트 루프를 막는 문제

Kubernetes 매니페스트와 Kubernetes 배포 절차는 이번 범위에서 제외한다.

## 결정한 접근법

### 공개 플레이어 UI

- `model-server/frontend/`에 React, TypeScript, Vite 기반 SPA를 둔다.
- 브라우저는 같은 호스트의 상대 경로 `/api/*`만 호출한다.
- API 호출에는 브라우저가 관리하는 `HttpOnly`, `Secure`, `SameSite=Lax` 세션 쿠키를 사용한다.
- 별도 클라이언트 상태 라이브러리는 초기 범위에 추가하지 않고 React reducer와 작은 API 모듈로 상태를 관리한다.
- 현재 `journal_showcase_styles.css`의 시각 토큰과 레이아웃을 재사용 가능한 CSS로 이식하되 사용자·모델 텍스트는 HTML 문자열이 아니라 React 텍스트 노드로 렌더링한다.

### Streamlit의 역할

- `player_app.py`는 공개 플레이어 런타임에서 제거한다.
- `test_app.py`와 관리자·디버그 화면은 개발 및 내부 운영 도구로 보존한다.
- 기본 Compose 배포에서는 Streamlit을 시작하지 않는다.
- 필요하면 별도 `tools` 프로필 또는 로컬 `uv run streamlit` 명령으로만 실행한다.
- 공개 Caddy 라우팅에는 Streamlit 경로를 두지 않는다.

### 배포 형태

- Node.js는 빌드 단계에서만 사용한다.
- 멀티스테이지 이미지가 프론트엔드를 빌드하고 최종 Caddy 이미지에는 정적 산출물만 포함한다.
- Caddy가 `/api/*`를 FastAPI로 프록시하고 나머지 경로에는 SPA 정적 파일을 제공한다.
- 브라우저와 API가 동일 출처이므로 CORS 의존성을 만들지 않는다.
- 기본 운영 서비스는 `web`, `api`, 선택적 `vllm`으로 단순화한다.

## 목표 아키텍처

```text
Browser
  | HTTPS 443
  v
Caddy web container
  |-- /, /assets/*  -> React static files
  `-- /api/*        -> FastAPI
                         |-- PostgreSQL: session, save, turn, quest, memory
                         |-- Neo4j: scoped knowledge retrieval
                         `-- vLLM: response and background memory summary
```

FastAPI는 계속해서 플레이어 상태와 데이터베이스의 유일한 경계다. 프론트엔드는 PostgreSQL, Neo4j, vLLM에 직접 접근하지 않는다.

## 세션 및 보안 설계

### 게스트 세션

1. 앱 최초 로드 시 브라우저가 `POST /api/sessions/bootstrap`을 호출한다.
2. 유효한 `hazel_session` 쿠키가 없으면 FastAPI가 guest player, default save, browser session을 생성한다.
3. 응답의 `Set-Cookie`가 동일 출처 브라우저에 직접 저장된다.
4. 새로고침, 브라우저 재접속, 프론트엔드 재배포 후에도 같은 쿠키로 기존 save를 복원한다.
5. bootstrap 응답은 현재 player/save 식별자와 CSRF 토큰 또는 안전한 쓰기 요청용 검증 값을 함께 제공한다.

### 쓰기 요청 보호

- `POST`, `PUT`, `PATCH`, `DELETE`는 허용된 `Origin`과 `Sec-Fetch-Site`를 확인한다.
- 세션 쿠키와 별도로 bootstrap에서 받은 CSRF 값을 `X-CSRF-Token` 헤더에 전송한다.
- 세션 쿠키는 JavaScript에서 읽지 못하도록 계속 `HttpOnly`로 유지한다.
- 계정 전환과 게임 턴은 공통 active-session 조회 함수를 사용한다.
- active session 조건은 token hash 일치, `revoked_at IS NULL`, `expires_at > now()`다.
- 만료·폐기된 세션은 계정 충돌이 아니라 `401 Unauthorized`로 처리한다.

### 기존 세션의 전환 한계

현재 Streamlit 구조에서는 FastAPI 세션 토큰이 브라우저에 저장되지 않았으므로 기존 Streamlit 게스트 세션을 새 프론트엔드가 자동 복원할 수 없다. 실제 운영 사용자가 이미 존재한다면 배포 전에 일회성 세션 이전 절차를 별도 승인해야 한다. 개발·데모 데이터라면 새 프론트엔드 최초 접속 시 새 guest session을 생성하는 것을 기본 전제로 한다.

## 턴 처리 및 idempotency 설계

### 프론트엔드 상태

각 전송은 브라우저에서 UUID 형식의 idempotency key를 한 번 생성한다. 전송 중인 payload와 key는 `sessionStorage`에 저장한다.

- `succeeded`: pending 정보를 삭제하고 대화를 다시 가져온다.
- `failed`: 오류 상태와 동일 key의 재시도 버튼을 표시한다.
- 네트워크 오류: 새 key를 만들지 않고 동일 key로 재시도한다.
- `llm_pending`: attempt ID를 저장하고 상태 조회 API로 복구한다.
- 새로고침: 저장된 pending attempt를 먼저 조회한 뒤 composer 상태를 결정한다.

### API 계약

- `POST /api/game/turns`는 응답 본문의 `status`를 권위 있는 상태로 제공한다.
- `GET /api/game/turns/{attempt_id}`를 추가해 새로고침, 네트워크 단절, 중복 요청을 복구한다.
- 실패 응답은 bounded `failure_code`와 사용자에게 노출 가능한 일반화된 메시지를 구분한다.
- 같은 idempotency key에 다른 NPC, quest, content를 보내면 `409 Conflict`를 반환한다.
- idempotency key의 형식과 최대 길이를 API 입력 단계에서 검증한다.

### 대화별 단일 진행 턴

동일 conversation에는 한 번에 하나의 `llm_pending` 턴만 허용한다.

1. 짧은 트랜잭션에서 conversation을 잠근다.
2. 기존 pending turn이 있으면 새로운 key의 턴을 시작하지 않고 활성 attempt를 반환하거나 `409 turn_in_progress`를 반환한다.
3. pending claim에는 시작 시각과 lease 만료 시각을 기록한다.
4. 제한 시간을 넘긴 stale pending은 명시적으로 failed로 전환한 뒤 재시도할 수 있다.
5. LLM 호출 동안 PostgreSQL 트랜잭션이나 row lock을 유지하지 않는다.
6. 응답 저장 시 attempt와 conversation을 다시 잠그고 claim 상태를 확인한 뒤 assistant message를 append한다.

이 정책은 여러 탭이나 직접 API 호출에서도 질문·답변 순서를 보장한다.

## 퀘스트 진행 설계

퀘스트 판정 코드를 Streamlit 소유 경로에서 FastAPI 도메인 경로로 옮긴다. 규칙 평가는 순수 함수로 유지하고 저장만 서비스 계층이 담당한다.

### 턴 흐름

1. 현재 `quest_progress`와 `observed_clues`를 읽는다.
2. 사용자 메시지와 현재 상태로 quest decision을 평가한다.
3. 전체 decision을 `turn_attempts.quest_decision`에 저장해 동일 key 재시도에서 재사용한다.
4. decision의 새 state, hint level, reveal truth, guidance로 Neo4j retrieval과 prompt를 구성한다.
5. LLM 성공 후 assistant message, `quest_progress`, 신규 `observed_clues`, attempt 성공 상태를 하나의 짧은 트랜잭션으로 저장한다.
6. Neo4j 또는 LLM 실패 시 decision snapshot은 남기되 quest progress와 observed clues는 적용하지 않는다.

### 규칙 경계

- answer-sensitive 지식은 decision과 저장된 quest state가 허용하기 전까지 차단한다.
- NPC, quest ID는 canonical rule set에 존재하는 값만 API가 허용한다.
- retry는 최초 요청에 저장된 quest ID와 decision을 사용한다.
- 동일 clue는 unique constraint와 upsert로 중복 저장하지 않는다.

## 메모리 압축 설계

assistant message와 턴 성공 상태를 커밋한 뒤 HTTP 응답을 먼저 반환한다. 메모리 압축은 별도의 DB session을 사용하는 응답 후 작업으로 실행한다.

- request-scoped AsyncSession을 백그라운드 작업에 전달하지 않는다.
- checkpoint compare-and-set을 유지해 중복 압축을 안전하게 무시한다.
- 압축 실패는 성공한 턴을 실패로 바꾸지 않는다.
- 백그라운드 작업이 프로세스 종료로 유실되어도 다음 성공 턴에서 압축 필요 여부를 다시 확인한다.
- 빈 summary는 checkpoint를 전진시키지 않는다.
- threshold와 retained count에는 양수 범위 검증을 추가한다.
- 장기적으로 강한 전달 보장이 필요해질 때만 PostgreSQL job table을 후속 도입한다. 초기 구현에는 Redis나 별도 queue를 추가하지 않는다.

## Neo4j 비동기 경계

- `GraphDatabase.driver`를 `AsyncGraphDatabase.driver`로 교체한다.
- retrieval protocol과 호출부를 `await graph.execute_query(...)` 형태로 통일한다.
- FastAPI lifespan에서 드라이버를 생성하고 종료 시 `await driver.close()`를 호출한다.
- health endpoint와 일반 세션 API는 느린 Neo4j 요청 때문에 이벤트 루프가 막히지 않아야 한다.

## 프론트엔드 화면 설계

### 컴포넌트

- `AppShell`: bootstrap, 전역 오류, 반응형 레이아웃
- `NpcRoster`: NPC 전환과 현재 선택 상태
- `NpcStatusHeader`: NPC 역할과 현재 목표
- `ConversationPanel`: 대화, empty/loading/failed 상태
- `QuestJournal`: quest state, hint level, 관찰한 단서, route recommendation
- `MessageComposer`: 전송, pending, retry, 입력 보존
- `TurnStatusNotice`: 실패 코드와 재시도 동작

### 상태 원칙

- 전송 중에는 현재 conversation composer를 잠그되 NPC 탐색은 허용한다.
- 전송 실패 시 사용자가 작성한 문장과 idempotency key를 보존한다.
- 서버 상태를 추측해서 성공으로 표시하지 않는다.
- route recommendation이 있으면 해당 NPC로 이동할 수 있지만 자동 이동은 사용자 선택을 존중한다.
- 모든 사용자 및 모델 문자열은 escaping되는 텍스트로 렌더링한다.

### UI/UX 보존

- 마을 통신 수첩, 양피지, 목재, 왁스 인장 시각 언어를 유지한다.
- 기존 375px, 768px, 1280px 반응형 기준을 유지한다.
- NPC 전환, composer, quest disclosure는 키보드로 조작할 수 있어야 한다.
- 최소 44px 터치 영역, `focus-visible`, reduced motion, 한국어 줄바꿈 기준을 유지한다.

## 오류 처리

| 상황 | API 상태 | 프론트엔드 동작 |
|---|---|---|
| 세션 만료 | 401 | bootstrap 한 번 재시도 후 복구 불가 시 세션 안내 |
| CSRF/Origin 실패 | 403 | 재전송하지 않고 보안 오류 표시 |
| 동일 key의 다른 payload | 409 | 로컬 pending 데이터 검증 오류 표시 |
| 다른 턴 진행 중 | 409 또는 pending attempt | 활성 턴 상태를 조회하고 composer 잠금 |
| Neo4j/vLLM 실패 | turn `failed` | 기존 질문과 key를 보존하고 재시도 제공 |
| 네트워크 단절 | 불명 | 같은 key로 상태 조회 후 재시도 |
| 메모리 압축 실패 | 성공 턴 유지 | 사용자에게 오류를 노출하지 않고 서버 로그 기록 |

## 테스트 전략

### 백엔드

- quest decision이 progress와 observed clue에 원자적으로 반영되는 통합 테스트
- 실패한 턴이 quest state를 전진시키지 않는 테스트
- 동일 key 재시도 및 payload 충돌 테스트
- 동일 conversation 동시 요청 순서 테스트
- stale pending lease 복구 테스트
- 만료된 세션의 game/account 접근 거부 테스트
- 백그라운드 메모리 압축 성공·실패·빈 summary 테스트
- 느린 Neo4j fake와 동시에 health/session 요청이 완료되는 async 테스트

### 프론트엔드

- bootstrap, 새로고침 복구, NPC 격리 테스트
- `failed`, `pending`, 네트워크 오류별 composer 상태 테스트
- 동일 idempotency key 재사용 테스트
- quest state와 route recommendation 렌더링 테스트
- 사용자·모델 입력 XSS 렌더링 테스트

### 브라우저 및 배포

- 실제 HTTPS 또는 secure-cookie를 재현한 환경에서 쿠키 유지 확인
- 375px, 768px, 1280px Playwright 시각·키보드 검증
- 새로고침, 뒤로 가기, 다중 탭, 느린 응답, 오프라인 전환 검증
- Compose에서 `web -> api -> database/model` smoke test
- 공개 경로에서 Streamlit 관리자 페이지에 접근할 수 없음을 확인

## 롤아웃 전략

1. 백엔드 계약과 quest/turn 안정화를 먼저 완료한다.
2. React 프론트엔드를 별도 preview 경로 또는 로컬 Compose에서 검증한다.
3. 기존 Streamlit 플레이어와 기능 동등성을 확인한다.
4. Caddy 기본 `/`를 React SPA로 전환한다.
5. 한 릴리스 동안 Streamlit 플레이어 소스와 이전 이미지 롤백 경로를 보존한다.
6. 운영 확인 후 공개 Streamlit player 서비스 정의만 제거하고 내부 도구는 유지한다.

## 완료 기준

- 새로고침 후 동일 guest save와 NPC 대화가 복구된다.
- 대화로 quest state, hint level, observed clues가 실제 DB에서 진행된다.
- failed/network timeout 후 동일 key 재시도가 메시지를 중복 생성하지 않는다.
- 동일 NPC에 동시 턴을 보내도 질문·답변 순서가 보존된다.
- 메모리 압축 시간이 턴 HTTP 응답 시간을 늘리지 않는다.
- 만료된 세션으로 게임 요청이나 계정 전환을 수행할 수 없다.
- 느린 Neo4j 요청 중에도 다른 API 요청이 이벤트 루프에서 처리된다.
- 공개 UI가 기존 게임풍 시각 품질과 접근성 기준을 유지한다.

## 비목표

- Kubernetes 파일 수정 또는 Kubernetes 배포
- PostgreSQL·Neo4j 저장소 역할 변경
- vLLM 모델 변경
- canonical story content 변경
- Redis, Kafka, Celery 도입
- 관리자 UI 전면 재작성
- 기존 Streamlit 디버그 도구 즉시 삭제
