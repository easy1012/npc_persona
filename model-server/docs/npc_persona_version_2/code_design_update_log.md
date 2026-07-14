# 코드 및 설계 수정 기록

## 2026-06-29 작업 시작 기록

### 무엇을

- Docker 기반 연속대화 질의 테스트를 실행하기 전, 작업 범위와 검증 시나리오를 고정했다.
- 리팩토링은 사용자 요청으로 중단된 상태이므로 이번 문서는 리팩토링이 아니라 연속대화 QA, 로그 분석, 필요한 최소 코드/설계 보정만 기록한다.

### 왜

- 여러 NPC가 각자 제한된 정보만 제공하고, 촌장 로완이 정보 부족 시 관련 NPC/퀘스트로 되돌리는 흐름을 실제 실행 표면에서 검증해야 한다.
- 이후 코드나 설계 수정이 발생하면 어떤 증거 때문에 바꿨는지 추적 가능해야 한다.

### 누가

- 작업자: Sisyphus.
- 승인자: 사용자.

### 언제

- 2026-06-29 작업 시작 시점.

### 어디서

- 프로젝트 루트: `C:\Users\HSM\Desktop\npc_persona\npc_persona`.
- 주요 대상: `src/streamlit/`, `compose.design-test.yaml`, `docs/npc_persona_version_2/`.

### 어떻게

- DB reset과 Docker volume 삭제 없이, `compose.design-test.yaml` 기반 로컬 검증 스택을 사용한다.
- 실제 `.env` 읽기는 승인됐지만 현재 `.env`와 `.env.design-test`는 없으므로 `.env.design-test.example`을 사용한다.
- 시나리오 계약은 happy path, 조기 최종추리 edge, 리오 데이터 품질, 회귀 테스트 보존으로 나누어 검증한다.

## 2026-06-29 Docker QA 및 UI 기본 라우팅 보정

### 무엇을

- `compose.design-test.yaml` 스택에서 Neo4j, vLLM, Streamlit을 실제 구동해 연속대화 QA를 수행했다.
- `q_jelly_color` 선택 시 첫 관찰 담당자인 `patrol_leader_rio`가 아니라 `mage_lumi`로 바로 동기화되어 리오의 색 변화 단서를 UI에서 시작하기 어려운 문제를 확인했다.
- `src/streamlit/quest_types.py`의 `QUEST_DEFAULT_NPC_IDS["q_jelly_color"]`를 `patrol_leader_rio`로 변경했다.
- 회귀 테스트 `test_script/test_quest_ui_defaults.py`를 추가해 q_jelly UI 기본 NPC 계약을 고정했다.

### 왜

- `q_jelly_color`의 `quest_steps` 첫 단계는 리오가 말랑 들판에서 평소보다 진한 방울젤리를 관찰하는 흐름이다.
- 기존 기본값은 루미였기 때문에 브라우저 QA에서 리오/q_jelly 조합을 만들기 어렵고, 사용자가 정상 시나리오를 따라도 `clue_jelly_color_change`가 누락될 수 있었다.

### 누가

- 작업자: Sisyphus.
- 승인자: 사용자. Docker 구동, live merge import, 테스트 실행, 필요한 수정 기록을 승인했다.

### 언제

- 2026-06-29 Docker design-test QA 중 발견 직후.

### 어디서

- 코드: `src/streamlit/quest_types.py`.
- 테스트: `test_script/test_quest_ui_defaults.py`.
- 실행 표면: `http://127.0.0.1:18501` Streamlit sidebar의 `Quest` 선택.

### 어떻게

- Playwright CLI로 Streamlit 페이지를 열고 `q_jelly_color` 선택 시 NPC/role 동기화 결과를 확인했다.
- 수정 후 Streamlit 이미지를 rebuild/recreate하고, 같은 UI 동작에서 `q_jelly_color -> patrol_leader_rio -> knight`로 동기화되는 것을 재확인했다.
- 검증 명령은 `uv run --frozen python -m unittest discover -s test_script -p "test_quest_*.py"`, `uv run --frozen python -m compileall src test_script`, `uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j`를 사용했다.

## 2026-06-29 데이터 증강 계약 테스트 및 importer count 보정

### 무엇을

- `test_script/test_story_source_contract.py`의 원천 데이터 계약을 26개 `KnowledgeChunk`에서 30개 `KnowledgeChunk`로 갱신했다.
- 같은 테스트에 네 개 신규 chunk ID와 퀘스트별 한국어 `story_expansion.six_w_log` 필수 조건을 추가했다.
- `src/db_control/import_story_source_to_neo4j.py`의 `EXPECTED_CHUNK_COUNTS`를 새 분포에 맞게 조정하고, validation error 문구가 기대 총합을 동적으로 표시하도록 바꿨다.
- `docs/.study`의 current MVP 학습 기준도 30개 `KnowledgeChunk` 기준으로 맞추고, `test_script/test_study_docs_contract.py`의 baseline term을 함께 갱신했다.

### 왜

- 데이터 증강이 실제로 canonical source에 반영됐는지 테스트로 고정해야 했다.
- importer는 작은 MVP 데이터셋의 고정 ID와 chunk 분포를 보호하는 안전장치이므로, 데이터가 30개로 증강된 뒤에도 dry-run validation이 새 계약을 기준으로 동작해야 했다.

### 누가

- 작업자: Sisyphus.
- 승인자: 사용자.

### 언제

- 2026-06-29, `rsc/data` 백업 후 canonical data 증강 직전과 직후.

### 어디서

- 테스트: `test_script/test_story_source_contract.py`, `test_script/test_quest_ui_defaults.py`.
- 학습 문서 테스트: `test_script/test_study_docs_contract.py`.
- importer: `src/db_control/import_story_source_to_neo4j.py`.
- 학습 문서: `docs/.study/01-project-baseline-current-mvp.md`, `05-neo4j-build-and-import.md`, `15-neo4j-executable-build-lab.md`.
- 기록 위치: `docs/npc_persona_version_2/code_design_update_log.md`.

### 어떻게

- TDD 순서로 먼저 테스트를 수정하고, 데이터 수정 전 `uv run --frozen python -m unittest test_script.test_story_source_contract test_script.test_quest_ui_defaults`가 30개 chunk 및 `six_w_log` 누락으로 실패하는 것을 확인했다.
- 데이터와 importer count 계약을 수정한 뒤 같은 테스트가 통과하는 것을 확인했다.
- Neo4j reset, Docker 재구동, live DB import, 커밋/푸시는 실행하지 않았다.

### 검증 결과

- `uv run --frozen python -m unittest test_script.test_story_source_contract test_script.test_quest_ui_defaults test_script.test_deployment_contract`: OK, 32 tests.
- `uv run --frozen python -m unittest test_script.test_study_docs_contract`: OK, 11 tests.
- `uv run --frozen python -m compileall src test_script`: PASS.
- `uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j`: PASS, `KnowledgeChunk: 30`.
- `uv run --frozen python scripts/story_pipeline/validate_data.py`: `Validation PASS`.
- `uv run --frozen basedpyright ...`와 `uv run --frozen ruff check ...`는 각각 실행 파일을 찾지 못해 실행하지 못했다.
- 전체 `test_script` discovery는 이번 증강 범위를 벗어난 기존 Streamlit 계약 실패를 포함해 실패했으므로, 이번 완료 기준은 위의 targeted regression, compileall, importer dry-run, data validator로 삼았다.

## 2026-06-30 개발 서버 퀘스트 진행 시나리오 QA

### 무엇을

- 개발 Docker 스택에서 유저 추리 기반 퀘스트 진행 프로세스를 검증했다.
- 각 NPC별 단서 진행과 최종 촌장 로완 시나리오를 기존 회귀 테스트로 확인했다.
- Streamlit 브라우저 표면은 Playwright CLI 반복 자동화 대신 실제 브라우저 창을 직접 열고 OS 스크린샷으로 정상 렌더링만 확인했다.

### 왜

- 사용자가 중요하다고 지정한 범위는 전체 UI 기능이 아니라 “유저가 추리하면서 NPC별 단서를 모으고, 로완이 부족한 근거를 되돌리거나 최종 정답을 인정하는 과정”이었다.
- Streamlit은 Playwright CLI snapshot/automation에서 abort 또는 반복 문제가 생길 수 있어, 브라우저 표면은 실제 창 확인으로 제한해야 했다.
- 개발 서버는 준비된 `google/gemma-4-E2B-it` 모델을 사용해야 하며, 운영용 `google/gemma-4-E4B-it` 다운로드 경로로 빠지면 안 됐다.

### 누가

- 작업자: Sisyphus.
- 승인자: 사용자. 긴 테스트는 3회 이상 타임아웃 시 기록하고 스킵하며, Streamlit 브라우저는 특히 조심하라고 지시했다.

### 언제

- 2026-06-30 개발 Docker 시나리오 QA 단계.

### 어디서

- 개발 Docker project: `hazel_design_test`.
- Streamlit: `http://127.0.0.1:18501`.
- vLLM model endpoint: `http://127.0.0.1:18000/v1/models`.
- Quest runtime 검증: `test_script.test_quest_auto_progression`, `test_script.test_quest_conversation_contract`.

### 어떻게

- `docker compose -f compose.design-test.yaml --env-file .env.design-test.example --profile gpu config`로 `MODEL_NAME=google/gemma-4-E2B-it`, 로컬 E2B 모델 마운트, 개발 포트 격리를 먼저 확인했다.
- vLLM `/v1/models`가 `google/gemma-4-E2B-it`만 반환하고, 컨테이너 환경의 `MODEL_NAME`도 E2B인지 확인했다.
- 개발 컨테이너 내부에서 `docker exec hazel_design_test-streamlit-1 uv run --frozen python -m unittest test_script.test_quest_auto_progression test_script.test_quest_conversation_contract`를 실행했다.
- 결과는 `Ran 20 tests in 1.095s`, `OK`였다.
- 테스트가 확인한 핵심 흐름은 민민 부인의 버섯/달빛 단서, 리오의 발자국/가루 및 표지판/뿌리 자국 단서, 루미의 방울젤리/마나 반응 단서, 로완의 부족 단서 라우팅과 최종 정답 승인이다.
- 로완 시나리오는 조기 최종추리 차단, 미완료 선행 퀘스트가 있을 때 관련 NPC로 되돌림, 모든 선행 단서 충족 후 `truth_moonwell_mana_cycle` 공개와 `solved` 전환을 확인했다.
- 실제 브라우저 창은 `Start-Process http://127.0.0.1:18501`로 열고 OS 스크린샷 `C:\Users\HSM\AppData\Local\Temp\codex-shot-2026-06-30_02-31-16.png`에서 Streamlit UI, 사이드바, 입력창이 정상 표시되고 blank/abort/error가 없음을 확인했다.

### 검증 결과

- 개발 스택 상태: Neo4j, Streamlit, vLLM 모두 healthy.
- 개발 모델: `/v1/models` 응답에 `google/gemma-4-E2B-it`만 존재.
- Quest runtime 시나리오: 20 tests OK.
- 직접 브라우저 표면: 정상 렌더링 확인.
- Playwright CLI 기반 반복 브라우저 QA는 Streamlit에서 무한 반복/abort 위험이 있어 중단하고 실제 창 확인으로 대체했다.

## 2026-06-30 로완 최종 응답 품질 보정 및 Admin 계약 갱신

### 무엇을

- `src/streamlit/prompting.py`의 로완 최종 전말 공개 지시를 강화했다.
- `src/streamlit/quest_rules.py`의 로완 partial guidance가 순찰대장 리오와 `바뀐 숲길 표지판`을 명시하도록 보정했다.
- `test_script/test_streamlit_prompting.py`, `test_script/test_quest_conversation_contract.py`, `test_script/test_streamlit_contract.py`의 계약을 최신 구조와 품질 기준에 맞췄다.
- 사용자 재현 문서 `docs/npc_persona_version_2/quest_scenario_reproduction_guide.md`를 추가했다.

### 왜

- 개발 E2B 모델 QA에서 로완 최종 턴이 `solved` 상태와 answer-sensitive retrieval은 맞았지만, 응답이 달빛 샘터 마나 주기와 선행 단서 연결을 충분히 명시하지 않는 품질 실패를 보였다.
- 로완 partial 턴은 route decision은 맞았지만, 실제 답변이 사용자를 어느 NPC/퀘스트로 보내야 하는지 충분히 분명하지 않을 수 있었다.
- Admin contract는 `QUEST_STATE_HINT_LEVELS`가 `test_app.py`에서 `quest_types.py`로 이동된 최신 구조를 반영하지 못했다.

### 누가

- 작업자: Sisyphus.
- 승인자: 사용자. 개발 서버 QA를 계속 진행하고, 운영 설정은 유지하라고 지시했다.

### 언제

- 2026-06-30 개발 Docker 품질 QA 중 Rowan final 품질 실패를 발견한 직후.

### 어디서

- Prompt 보정: `src/streamlit/prompting.py`.
- Rule guidance 보정: `src/streamlit/quest_rules.py`.
- 테스트: `test_script/test_streamlit_prompting.py`, `test_script/test_quest_conversation_contract.py`, `test_script/test_streamlit_contract.py`.
- 품질 QA 보고서: `output/reports/quest_scenario_quality_20260630.md`.
- 재현 문서: `docs/npc_persona_version_2/quest_scenario_reproduction_guide.md`.

### 어떻게

- TDD로 먼저 prompt/guidance 기대 문구가 없을 때 실패하는 것을 확인했다.
- 최종 공개 허용과 `quest_state == "solved"`가 동시에 충족될 때 `[최종 전말 공개 지시]`를 넣고, 첫 문장부터 전말을 확정하며 되묻지 않도록 했다.
- 로완 partial guidance는 누락 단서가 있는 경우 순찰대장 리오에게 `바뀐 숲길 표지판`의 남은 단서를 확인하라고 안내하도록 조정했다.
- Admin 구조 계약은 `QUEST_STATE_HINT_LEVELS` 정의 위치를 `src/streamlit/quest_types.py`로 확인하도록 갱신했다.
- Admin 표면은 `streamlit.testing.v1.AppTest`로 `persona_chat admin`, 세 탭, Quest State selectbox, Save Quest State button, Allowed Hint Level metric이 예외 없이 렌더링되는지 확인했다.

### 검증 결과

- `uv run --frozen python -m unittest test_script.test_streamlit_contract.StreamlitContractTest.test_admin_controls_live_on_separate_streamlit_page test_script.test_streamlit_contract.StreamlitContractTest.test_quest_state_synchronizes_hint_level`: OK, 2 tests.
- `test_script/run_quest_scenario_quality.py`: `PASS quality QA records=11`, model `google/gemma-4-E2B-it`, final state `solved`.
- Admin surface check: `exceptions=0`, tabs `Memory Admin`, `Quest Admin`, `Concept Story Admin`, metric `Allowed Hint Level` 확인.
- `basedpyright`와 `ruff`는 현재 실행 파일이 없어 실행하지 못했다.
