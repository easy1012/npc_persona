# 헤이즐 마을 웹 프론트엔드 전환 및 런타임 안정화 구현 계획

## 범위와 원칙

- 공개 플레이어 화면을 React/TypeScript SPA로 전환한다.
- Streamlit은 내부 관리자·디버그 도구로만 유지한다.
- FastAPI, PostgreSQL, Neo4j, vLLM의 기존 소유 경계를 유지한다.
- Kubernetes는 수정·검증·문서 갱신 대상에서 제외한다.
- 각 단계는 테스트 우선으로 진행하고, 다음 단계로 넘어가기 전에 해당 단계의 회귀 테스트를 통과시킨다.
- 기존 dirty worktree와 사용자의 staged 변경을 보존한다. 구현 커밋은 기능별로 분리한다.

## 0단계: 기준선과 의사결정 고정

### 작업

1. 현재 `origin/main...hsm_branch`와 staged 변경을 별도로 기록한다.
2. 기존 테스트 명령과 실패 원인을 기준선 문서에 남긴다.
3. 공개 플레이어 UI의 필수 기능 목록을 고정한다.
   - guest bootstrap 및 복구
   - NPC별 대화 격리
   - 턴 전송·pending·failed·retry
   - quest state, hint, observed clue, route 표시
   - 반응형·키보드·reduced motion
4. 기존 Streamlit guest session을 새 브라우저 쿠키로 이전할 필요가 있는지 배포 전에 결정한다.

### 검증

- `uv run ruff check src/game_service tests`
- `uv run basedpyright --level error src/game_service tests`
- `powershell -ExecutionPolicy Bypass -File scripts/test_memory.ps1`
- 모델 및 데이터베이스 contract 테스트 결과 기록

### 완료 조건

- 기능 범위, 세션 이전 정책, 테스트 기준선이 승인된다.

## 1단계: API 계약과 공통 오류 모델 정리

### 대상 파일

- `src/game_service/schemas.py`
- `src/game_service/routers/game.py`
- `src/game_service/routers/sessions.py`
- 신규 `src/game_service/errors.py` 또는 동등한 오류 모듈
- 관련 API 계약 테스트

### 작업

1. `TurnResponse`에 `status`, `attempt_id`, `failure_code`, conversation snapshot을 명확히 정의한다.
2. `GET /api/game/turns/{attempt_id}`를 추가한다.
3. attempt 조회 시 현재 session principal의 save/conversation 소유권을 검증한다.
4. idempotency key를 UUID 또는 제한된 128자 이하 형식으로 검증한다.
5. 동일 key 요청의 NPC, quest, content fingerprint가 다르면 `409 idempotency_conflict`를 반환한다.
6. 알려지지 않은 NPC와 quest ID는 DB에 쓰기 전에 `422`로 거부한다.
7. 오류 응답에 안정적인 machine code를 추가하고 내부 예외 문자열은 직접 노출하지 않는다.

### 테스트

- 잘못된 NPC/quest/key 입력이 DB row를 만들지 않는다.
- 다른 save의 attempt를 조회하면 404 또는 403을 반환한다.
- 동일 key와 동일 payload는 같은 attempt를 반환한다.
- 동일 key와 다른 payload는 409를 반환한다.
- succeeded, failed, pending response schema를 각각 검증한다.

### 완료 조건

- 프론트엔드가 HTTP 코드만 추측하지 않고 응답 상태로 복구할 수 있다.

## 2단계: 세션 검증 통합과 브라우저 보안

### 대상 파일

- `src/game_service/services/session_service.py`
- `src/game_service/services/account_service.py`
- `src/game_service/routers/accounts.py`
- `src/game_service/routers/game.py`
- `src/game_service/routers/sessions.py`
- 세션 및 계정 테스트

### 작업

1. token hash, revoked, expiry를 한 번에 검사하는 `load_active_browser_session`을 만든다.
2. game principal 조회와 account conversion이 같은 active-session 함수를 사용하게 한다.
3. 만료·폐기 세션은 account conflict가 아니라 401로 변환한다.
4. bootstrap이 프론트엔드에 필요한 CSRF 값을 반환하도록 한다.
5. unsafe method에 Origin, Sec-Fetch-Site, CSRF 검증 dependency를 적용한다.
6. 운영 HTTPS와 로컬 개발 HTTP의 cookie secure 정책을 명시적인 environment setting으로 구분하되 운영 기본값은 secure로 둔다.
7. session rotation 후 기존 CSRF 값도 폐기한다.

### 테스트

- 만료된 세션으로 game state, turn, account conversion이 모두 거부된다.
- revoked session도 동일하게 거부된다.
- 허용되지 않은 Origin과 누락된 CSRF header가 거부된다.
- 정상 same-origin 요청은 허용된다.
- account conversion이 session과 CSRF를 함께 회전한다.

### 완료 조건

- 브라우저 쿠키를 직접 사용하는 모든 쓰기 요청이 동일한 인증·CSRF 정책을 따른다.

## 3단계: 퀘스트 엔진을 FastAPI 도메인으로 이동

### 대상 파일

- `src/streamlit/quest_rules.py`, `quest_loader.py`, `quest_types.py`의 순수 규칙 부분
- 신규 `src/game_service/domain/quests/`
- 신규 또는 수정 `src/game_service/services/quest_service.py`
- `src/game_service/services/turn_service.py`
- `src/game_service/models.py`
- 필요 시 Alembic migration

### 작업

1. Streamlit에 의존하지 않는 quest type, loader, rule evaluator를 game service domain으로 이동한다.
2. Streamlit 디버그 앱은 새 domain 모듈을 import하게 해 규칙 구현을 하나만 유지한다.
3. 현재 save의 `QuestProgress`와 `ObservedClue`를 domain 입력으로 변환한다.
4. 사용자 메시지를 평가해 full `QuestDecision`을 만든다.
5. 최초 attempt 생성 시 decision snapshot과 request fingerprint를 저장한다.
6. retry는 저장된 decision을 재사용하며 새 입력으로 재평가하지 않는다.
7. retrieval과 prompt가 decision의 state, hint, guidance, reveal truth를 사용하게 한다.
8. LLM 성공 트랜잭션에서 assistant message, progress, clue, attempt 성공을 함께 저장한다.
9. 실패 시 progress와 clue가 전진하지 않는지 보장한다.

### 테스트

- 기존 quest scenario matrix를 domain 테스트로 재사용한다.
- 첫 단서, 두 번째 단서, ready-to-answer, solved 전이를 DB 통합 테스트로 검증한다.
- 로완의 불완전 추리가 route recommendation만 반환하고 solved가 되지 않는지 검증한다.
- answer-sensitive chunk가 허용 전에는 조회되지 않는지 검증한다.
- 동일 key retry가 clue와 progress를 중복 적용하지 않는지 검증한다.
- LLM 실패 후 progress와 observed clue가 변하지 않는지 검증한다.

### 완료 조건

- public FastAPI 경로에서 대화만으로 quest와 clue가 실제로 진행된다.

## 4단계: 대화별 단일 pending claim과 순서 보장

### 대상 파일

- `database-server/schema.py`
- 신규 Alembic migration
- `src/game_service/models.py`
- `src/game_service/routers/game.py`
- `src/game_service/services/turn_service.py`
- 동시성 통합 테스트

### 작업

1. `turn_attempts`에 `started_at`, `lease_expires_at`, `completed_at`, request fingerprint를 추가한다.
2. conversation별 pending claim을 짧은 row-lock transaction에서 검사한다.
3. 다른 key의 유효한 pending attempt가 있으면 새 user message를 저장하지 않는다.
4. 같은 key는 기존 attempt와 user message를 재사용한다.
5. stale lease는 failed 상태와 bounded failure code로 전환한다.
6. LLM 호출 동안 transaction을 닫는다.
7. assistant append 시 conversation과 attempt를 다시 잠그고 유효한 claim인지 확인한다.
8. assistant ordinal은 성공한 turn 순서와 질문 순서가 일치하도록 attempt claim 순서에 따라 결정한다.

### 테스트

- 동일 conversation에 두 요청을 동시에 보내도 assistant 순서가 역전되지 않는다.
- 두 번째 요청이 첫 번째 user message와 섞이지 않는다.
- 다른 NPC conversation은 동시에 진행할 수 있다.
- stale pending이 복구되고 새 요청이 진행된다.
- 동일 key의 동시 재요청이 message를 한 번만 만든다.

### 완료 조건

- 다중 탭과 직접 API 호출에서도 한 NPC 대화의 질문·답변 순서가 보존된다.

## 5단계: 메모리 압축을 HTTP 응답에서 분리

### 대상 파일

- `src/game_service/services/memory_service.py`
- `src/game_service/services/memory_repository.py`
- `src/game_service/services/turn_service.py`
- `src/game_service/db.py`
- 메모리 단위·통합 테스트

### 작업

1. 성공 턴 커밋 직후 API response를 만들고 압축은 response 이후 실행되게 한다.
2. background compaction은 session factory에서 독립 AsyncSession을 생성한다.
3. request session과 ORM instance를 background task로 넘기지 않고 UUID 기반 scope만 전달한다.
4. 기존 checkpoint CAS로 중복 작업을 방지한다.
5. summary가 빈 문자열이면 checkpoint ordinal을 전진시키지 않는다.
6. threshold와 retained count가 유효한 양수인지 검증한다.
7. compaction 실패는 구조화 로그와 metric만 남기고 turn 상태를 바꾸지 않는다.
8. 다음 성공 턴이 미실행 compaction을 다시 감지하게 한다.

### 테스트

- 느린 summary fake를 사용해 turn response가 summary 완료를 기다리지 않는지 검증한다.
- summary 실패 후에도 turn status와 assistant message가 succeeded로 유지된다.
- background session이 request session 종료 후 정상 동작한다.
- 빈 summary와 invalid threshold가 checkpoint 손실을 만들지 않는다.
- 동시 compaction에서 하나만 checkpoint를 전진시킨다.

### 완료 조건

- 메모리 압축 LLM 시간이 플레이어 턴 응답 시간에 포함되지 않는다.

## 6단계: Neo4j async driver 전환

### 대상 파일

- `src/game_service/clients.py`
- `src/game_service/services/retrieval_service.py`
- `src/game_service/main.py`
- retrieval 및 lifespan 테스트

### 작업

1. graph protocol을 async `execute_query` 계약으로 변경한다.
2. `AsyncGraphDatabase.driver`를 사용한다.
3. FastAPI lifespan에서 driver를 생성·공유·종료한다.
4. fake graph와 기존 테스트 doubles를 async 형태로 변경한다.
5. Neo4j timeout과 retry 가능한 예외를 turn failure code에 안전하게 매핑한다.

### 테스트

- 느린 graph fake가 실행되는 동안 health와 session endpoint가 완료된다.
- lifespan 종료 시 driver close가 한 번 호출된다.
- Neo4j timeout이 turn failed로 기록되고 assistant message를 만들지 않는다.
- 기존 retrieval gate 테스트가 모두 통과한다.

### 완료 조건

- Neo4j I/O가 FastAPI 이벤트 루프를 동기적으로 차단하지 않는다.

## 7단계: React/TypeScript 프론트엔드 기반 구축

### 신규 구조

```text
model-server/frontend/
|-- package.json
|-- vite.config.ts
|-- tsconfig.json
|-- src/
|   |-- api/
|   |-- components/
|   |-- state/
|   |-- styles/
|   |-- test/
|   `-- App.tsx
`-- public/
```

### 작업

1. React, TypeScript, Vite와 최소 테스트 도구를 설정한다.
2. `/api` 상대 경로와 same-origin credentials를 사용하는 typed API client를 작성한다.
3. bootstrap과 active NPC 상태를 관리하는 reducer를 만든다.
4. current Streamlit UI를 다음 컴포넌트로 이식한다.
   - AppShell
   - NpcRoster
   - NpcStatusHeader
   - ConversationPanel
   - QuestJournal
   - MessageComposer
   - TurnStatusNotice
5. 기존 디자인 토큰과 CSS를 이식하고 Streamlit selector 의존성을 제거한다.
6. 서버 text는 React text node로 렌더링하며 raw HTML 주입을 금지한다.

### 테스트

- API client request, cookie credentials, response parsing 테스트
- bootstrap loading/error/success 컴포넌트 테스트
- NPC 전환과 conversation 격리 테스트
- 빈 대화와 quest 없음 상태 테스트
- XSS payload가 HTML로 실행되지 않는 테스트

### 완료 조건

- mock API 기준으로 기존 플레이어 화면의 모든 상태가 동작한다.

## 8단계: 실패·pending·retry UX 구현

### 작업

1. 전송 전에 idempotency key와 payload를 `sessionStorage`에 저장한다.
2. 응답 body의 turn status를 반드시 파싱한다.
3. succeeded일 때만 pending 데이터를 삭제한다.
4. failed와 network error는 동일 key retry를 제공한다.
5. pending 상태는 attempt 조회 API로 polling하되 지수 backoff와 최대 UI 대기 시간을 둔다.
6. 새로고침 시 pending attempt를 먼저 복구한다.
7. conversation별 composer 잠금과 전송 중 안내를 표시한다.
8. 401은 bootstrap을 한 번만 재시도하고 무한 재시도를 방지한다.

### 테스트

- failed 202 응답을 성공으로 표시하지 않는다.
- 네트워크 오류 후 retry가 같은 key를 사용한다.
- 새로고침 후 pending 상태가 복구된다.
- 다른 NPC의 composer 상태와 섞이지 않는다.
- 중복 클릭이 요청을 두 번 만들지 않는다.

### 완료 조건

- 사용자가 실패 원인을 이해하고 메시지 중복 없이 복구할 수 있다.

## 9단계: Quest Journal과 게임 UI 기능 동등성

### 작업

1. API game state에 observed clue와 route recommendation을 포함한다.
2. QuestJournal에 state, hint tier, clue, 다음 NPC 안내를 표시한다.
3. route recommendation 버튼으로 대상 NPC를 선택할 수 있게 한다.
4. desktop 3열, tablet 2열, mobile 1열 레이아웃을 이식한다.
5. 키보드 NPC 이동, focus-visible, 44px target, reduced motion을 구현한다.
6. 긴 한국어 메시지와 매우 긴 단어의 wrapping을 검증한다.

### 테스트

- 375px, 768px, 1280px에서 overflow가 없다.
- 키보드만으로 NPC 선택, quest disclosure, 전송이 가능하다.
- 색상 없이도 active/failed/solved 상태를 구분할 수 있다.
- route recommendation이 올바른 NPC를 선택한다.

### 완료 조건

- Streamlit 플레이어 화면의 기능과 시각 품질을 충족하거나 개선한다.

## 10단계: Compose와 Caddy 전환

### 대상 파일

- 신규 frontend build Dockerfile
- `Caddyfile`
- `compose.yaml`
- `.dockerignore`
- `.env.example`
- `README.md`, `docs/deployment.md`
- Kubernetes 파일은 제외

### 작업

1. Node build stage와 Caddy runtime stage로 정적 web 이미지를 만든다.
2. Caddy가 `/api/*`를 api service로 전달하고 나머지는 SPA fallback으로 제공하게 한다.
3. 기본 Compose에서 공개 Streamlit service를 제거한다.
4. Streamlit 디버그 도구는 `tools` 프로필 또는 로컬 실행 문서로 옮긴다.
5. web healthcheck와 api dependency를 설정한다.
6. 프론트엔드에는 내부 API 주소를 노출하지 않고 상대 `/api`만 사용한다.
7. rollback을 위해 한 릴리스 동안 이전 Streamlit player 이미지 실행 방법을 문서에 남긴다.

### 검증

- `docker compose --env-file .env config`
- web과 api healthcheck
- HTTPS 접속 후 session cookie 속성 확인
- SPA deep link 새로고침 확인
- 공개 URL에서 Streamlit admin 접근 불가 확인
- non-GPU 기동과 선택적 vLLM 기동 절차 확인

### 완료 조건

- Node 런타임 없이 Caddy 정적 UI와 FastAPI가 기본 Compose로 배포된다.

## 11단계: 종합 QA와 롤아웃

### 자동 검증

1. Python Ruff, BasedPyright, 단위·통합·contract 테스트
2. 프론트엔드 lint, typecheck, unit test, production build
3. Playwright desktop/tablet/mobile 테스트
4. Compose smoke test
5. 동시 턴, 느린 Neo4j, 느린 vLLM, summary 실패 fault-injection 테스트

### 수동 시나리오

1. 첫 방문 후 대화하고 브라우저를 완전히 닫았다가 복구한다.
2. NPC 네 명의 대화를 오가며 transcript 격리를 확인한다.
3. 단서를 순서대로 제시해 quest state와 hint가 전진하는지 확인한다.
4. final reveal 전후의 answer-sensitive 지식 차단을 확인한다.
5. 네트워크를 끊었다가 동일 메시지를 재시도해 중복이 없는지 확인한다.
6. 다중 탭에서 같은 NPC에 동시에 전송해 순서 보장을 확인한다.
7. 만료된 cookie와 잘못된 Origin/CSRF 요청을 확인한다.
8. 375px, 768px, 1280px에서 한국어 UI와 키보드 탐색을 확인한다.

### 롤아웃

1. preview 환경에서 API와 React UI를 병행 검증한다.
2. DB migration을 먼저 적용한다.
3. API를 배포하고 이전 Streamlit player와 호환되는 read 경로를 확인한다.
4. web/Caddy를 배포해 `/`를 React로 전환한다.
5. 로그에서 401, 409, failed turn, compaction failure를 관찰한다.
6. 문제가 있으면 Caddy 라우팅을 이전 Streamlit player로 되돌린다.
7. 안정화 후 공개 Streamlit player 배포 정의를 정리한다.

## 권장 커밋 단위

1. `test: define active-session and turn-response contracts`
2. `fix: reject expired sessions and enforce csrf`
3. `feat: persist quest decisions and observed clues`
4. `fix: serialize pending turns per conversation`
5. `refactor: move memory compaction after response`
6. `refactor: use async neo4j driver`
7. `feat: add react player frontend shell`
8. `feat: add resilient turn retry and quest journal`
9. `deploy: serve player spa through caddy`
10. `test: add end-to-end player recovery scenarios`

## 최종 승인 체크리스트

- [ ] Kubernetes 변경이 포함되지 않았다.
- [ ] 동일 브라우저의 guest save가 새로고침 후 복구된다.
- [ ] account conversion이 만료 세션을 거부한다.
- [ ] quest progress와 observed clue가 FastAPI 경로에서 저장된다.
- [ ] failed/network retry가 동일 idempotency key를 사용한다.
- [ ] 한 conversation에 동시 pending turn이 생기지 않는다.
- [ ] 메모리 압축이 HTTP 응답을 지연하지 않는다.
- [ ] Neo4j 호출이 async event loop를 막지 않는다.
- [ ] 공개 UI에 관리자·디버그 기능이 노출되지 않는다.
- [ ] 375px, 768px, 1280px 브라우저 QA가 통과한다.
- [ ] 기존 사용자 staged 변경을 덮어쓰거나 함께 커밋하지 않았다.
