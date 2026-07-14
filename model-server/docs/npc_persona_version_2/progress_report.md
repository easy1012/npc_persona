# NPC Persona Version 2 Progress Report

## 2026-06-28 중간 보고 1

### 완료

- 현재 수동 퀘스트 진행 구조를 확인했다.
- 메인 앱은 `src/streamlit/test_app.py`에서 `quest_state_by_quest`와 `allowed_hint_level_by_quest`를 세션 상태로 관리한다.
- Admin 페이지는 `src/streamlit/pages/admin.py`에서 Memory Admin, Quest Admin, Concept Story Admin을 제공한다.
- 지식 조회는 `get_allowed_chunks()`에서 `hint_level`과 `answer_sensitive`를 기준으로 차단한다.
- 원천 데이터의 `story_expansion.quest_steps`, `unlocked_clue_ids`, `wrong_hypotheses`, `answer_reveal_policy`가 자동 진행 규칙의 기반으로 사용 가능함을 확인했다.
- LangGraph 공식 문서에서 `StateGraph`, `compile()`, `InMemorySaver`, `thread_id` 체크포인트 패턴을 확인했다.
- Context7 문서 조회는 quota 초과로 실패해 LangChain/LangGraph 공식 웹 문서와 librarian 탐색으로 보완 중이다.

### 기획 변경 반영

- 테스트 작성/실행, Streamlit 구동 테스트, Docker 구동 테스트는 모든 구현 완료 후 사용자 최종 승인을 받은 뒤에만 진행한다.
- 승인 전에는 문서, 구현, 설정 문서 작성까지만 수행한다.
- Docker를 구동한 경우 모든 작업 종료 전 반드시 종료해 VRAM을 회수한다.

### 다음 작업

- 자동 진행 순수 규칙 모듈 설계.
- LangGraph checkpoint runtime 설계.
- Streamlit 연결 지점 최소 변경 설계.
- E2B 개발용 Docker/env 문서와 설정 초안 작성.

## 2026-06-28 중간 보고 2

### 완료

- 운영 기본 `compose.yaml`와 `.env.example`은 `google/gemma-4-E4B-it` 기준으로 유지했다.
- 분리 검증 스택 `.env.design-test.example`와 `compose.design-test.yaml`은 Windows 16GB VRAM 개발 QA용 `google/gemma-4-E2B-it` 기본값으로 조정했다.
- `VLLM_GPU_MEMORY_UTILIZATION=0.82`, `VLLM_MAX_MODEL_LEN=3072`를 개발용 보수 기본값으로 문서화했다.
- `docs/design_test_docker.md`와 `docs/deployment.md`에 승인 전 Docker 구동 금지와 구동 후 teardown 의무를 반영했다.

### 아직 하지 않은 일

- 사용자 최종 승인 전이므로 compose config 확인, Docker up, health check, vLLM 호출은 실행하지 않았다.

### 현재 리스크

- 테스트 게이트가 승인 후로 이동했으므로 구현 직후 자동 검증 증거는 아직 만들지 않는다.
- 기존 `test_app.py`가 큰 파일이므로 자동 진행 로직은 별도 모듈에 두고 앱 연결부만 얇게 유지해야 한다.
- `docs/quest_auto_progression_plan.md`의 과거 “구현 금지” 문구는 이번 v2 지시로 대체된다.

## 2026-06-28 중간 보고 3

### 완료

- `langgraph>=1.0.0` 의존성을 추가하고 `uv.lock`을 갱신했다.
- 자동 퀘스트 진행 로직을 `src/streamlit/quest_types.py`, `quest_loader.py`, `quest_rules.py`, `quest_graph.py`, `quest_runtime.py`로 분리했다.
- Streamlit 메인 앱에서 명시적 퀘스트 선택, NPC별 route button, 퀘스트 진행 초기화, `answer_reveal_allowed` 기반 조회 차단을 연결했다.
- `src/streamlit/prompting.py`에 퀘스트 진행 안내와 정답 공개 권한 문구를 추가했다.
- `src/streamlit/pages/admin.py`는 공유 quest/NPC 상수를 새 타입 모듈에서 가져오도록 정리했다.
- route button은 유효하지 않은 route target을 무시하고, 유효한 경우 NPC와 역할만 변경하면서 현재 퀘스트 문맥을 유지하도록 점검했다.

### 아직 하지 않은 일

- 사용자 최종 승인 전이므로 테스트 작성/실행, LSP diagnostics, compile/import check, Streamlit 구동, Docker 구동, vLLM 호출, health check는 실행하지 않았다.
- Docker stack은 이번 구현 중 구동하지 않았다.

### 승인 후 검증 계획

- 변경된 Python 파일 diagnostics와 import/compile 수준 확인을 실행한다.
- 자동 진행 규칙과 LangGraph runtime에 대한 최소 테스트를 추가하거나 실행한다.
- 필요 시 Streamlit을 실제로 띄워 NPC route, 퀘스트 선택, 정답 공개 차단/해제 흐름을 확인한다.
- Docker/vLLM 검증을 승인받아 실행한 경우 작업 종료 전 반드시 stack을 종료한다.

## 2026-06-28 중간 보고 4

### Oracle 검증 실패 후 보완

- SC-01부터 SC-08까지의 자동 진행 계약을 `tests/test_quest_auto_progression.py`에 stdlib `unittest`로 고정했다.
- 자연어 근거 문장이 `quest_steps[].unlocked_clue_ids`를 너무 문자 그대로만 매칭하던 문제를 보완했다.
- 단서명/단계 문장 fuzzy token matching에서 한 단어만 겹쳐도 다른 단서가 열리던 문제를 막았다. 예: `밝은 버섯`이 `달 밝은 밤`까지 즉시 해금하지 않도록 조정했다.
- 같은 LangGraph `thread_id` 호출에서 이전 checkpoint의 `observed_clue_ids_by_quest`를 병합하도록 `run_quest_turn()`을 보완했다.
- 서로 다른 NPC/퀘스트 thread는 기존처럼 단서가 섞이지 않도록 유지했다.
- 비촌장 NPC가 로완에게 최종 종합 추리를 유도할 때 `route_to_npc_id`와 함께 `route_to_quest_id=q_main_spore_night`도 전달하도록 보완했다.

### 확인한 계약

- SC-01: 비촌장 NPC에게 정황 근거를 제시하면 해당 단계 단서가 해금되고 truth reveal은 열리지 않는다.
- SC-02: 비촌장 NPC에게 최종 추리를 말하면 `chief_rowan`으로 route하고 `solved`로 만들지 않는다.
- SC-02 추가 확인: 로완 이동 시 최종 종합 퀘스트 `q_main_spore_night` 문맥도 함께 전달한다.
- SC-03: 로완에게 충분한 최종 근거를 제시하면 `solved`, hint level 3, reveal truth가 반환된다.
- SC-04: 로완에게 부분/오답 추리를 제시하면 빠진 단서와 관련 NPC로 되돌린다.
- SC-05: 같은 `thread_id`는 이전 단서를 기억한다.
- SC-06: 다른 NPC/퀘스트 thread는 단서를 공유하지 않는다.
- SC-07: Admin 페이지의 Memory Admin, Quest Admin, Concept Story Admin과 수동 Quest override 문맥을 유지한다.
- SC-08: `get_allowed_chunks()`의 hint level 및 `answer_sensitive` 공개 gate를 유지한다.

### 실행한 검증

- `uv run --frozen python -m unittest tests.test_quest_auto_progression`: PASS, 9 tests.
- `uv run --frozen python -m compileall src/streamlit tests`: PASS.

## 2026-06-28 중간 보고 5

### Oracle 재검증 전 보완

- Oracle이 지적한 false-positive 최종 판정 문제를 회귀 테스트로 고정했다.
- 로완에게 모든 단서가 관측된 상태여도 사용자가 “정답은 잘 모르겠다”처럼 실제 연결 추리를 말하지 않으면 `solved`와 truth reveal이 발생하지 않도록 수정했다.
- 최종 정답 판정에서 관측 단서는 “자격 조건”으로만 쓰고, 사용자 메시지에 answer truth와 단서 연결이 실제로 들어 있을 때만 완료되도록 조정했다.
- Admin/수동 override로 `ready_to_answer`가 설정된 퀘스트가 다음 자동 평가에서 단서 부족 때문에 `hint_1_given` 등으로 내려가지 않도록 상태 전이를 단조 증가 방식으로 보정했다.
- 로완이 부분/오답 추리에서 빠진 단서로 되돌릴 때 관련 NPC뿐 아니라 관련 퀘스트(`route_to_quest_id`)도 함께 반환하도록 보완했다.

### 추가 검증

- `uv run --frozen python -m unittest discover -s tests -p "test_*.py"`: PASS, 11 tests.
- `uv run --frozen python -m compileall src/streamlit tests`: PASS.
- `uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j`: PASS, NPC 4 / Location 8 / Quest 5 / Role 4 / Event 5 / Clue 8 / Truth 3 / KnowledgeChunk 26.

### 여전히 실행하지 않은 것

- Streamlit UI 구동, Docker stack 구동, vLLM 호출, health check는 실행하지 않았다.
- Docker를 켜지 않았으므로 종료할 container도 없다.

## 2026-06-28 최종 검증 보고

### Oracle 재검증 결과

- Oracle 재검증에서 `<promise>VERIFIED</promise>`를 받았다.
- MVP 구현 단계 기준으로 자동 근거 기반 퀘스트 진행, 로완 최종 라우팅, 로완 정답/부분정답 분기, Admin 유지, LangGraph checkpoint continuity, answer-sensitive 공개 gate가 충분하다는 판정을 받았다.

### 남은 한계

- 한국어 의미 판정은 아직 canonical 단서/truth 문구 중심의 substring/token matching이다. 실제 사용자 paraphrase 대응을 강화하려면 이후 단계에서 clue alias/rubric 또는 구조화된 LLM adjudicator를 추가해야 한다.
- LangGraph는 현재 `InMemorySaver` 기반 MVP checkpoint이며, 다중 사용자/재시작 내구성이 필요하면 SQLite/Postgres checkpointer로 확장해야 한다.
- Streamlit UI, Docker, vLLM smoke test는 이번 closeout에서 실행하지 않았다. Docker stack을 켜지 않았으므로 VRAM 회수를 위한 teardown 대상도 없다.

## 2026-06-28 추가 Oracle 지적 보완

### 보완 내용

- 자연어 paraphrase 최종 추리도 로완이 정답으로 인정할 수 있도록 `truth_moonwell_mana_cycle` 중심의 MVP rubric marker를 추가했다.
- 모든 단서가 있어도 canonical truth 이름을 직접 말하지 않으면 무조건 오답 처리되던 문제를 보완했다. 예: “달빛에 포자가 반응해서 버섯이 빛나고, 돼지가 숲으로 가고, 젤리 색과 표지판 변화도 같은 밤의 영향...” 흐름을 정답으로 인정한다.
- 잘못된 최종 추리에서 `missing`이 비어 있을 때 무조건 첫 번째 필수 단서로 되돌리던 문제를 보완했다. wrong hypothesis token score를 비교해 실제 오답 가설에 맞는 반증 단서/NPC/퀘스트로 route한다.
- 마지막 pre-final 퀘스트가 현재 턴에서 `ready_to_answer`가 되는 경우에도 즉시 로완과 `q_main_spore_night`로 route하도록, current turn의 prospective state map을 기준으로 `_all_pre_final_ready()`를 평가한다.

### 추가 회귀 테스트

- 자연어 paraphrase 최종 정답 수락.
- “마법 현상 하나가 모든 행동을 지배했다” 오답을 물리 증거 담당 NPC/퀘스트로 되돌림.
- 마지막 pre-final 퀘스트가 현재 턴에서 완료 조건을 충족하면 같은 턴에 로완으로 route.

### 추가 검증

- `uv run --frozen python -m unittest discover -s tests -p "test_*.py"`: PASS, 14 tests.
- `uv run --frozen python -m compileall src/streamlit tests`: PASS.
- `uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j`: PASS, NPC 4 / Location 8 / Quest 5 / Role 4 / Event 5 / Clue 8 / Truth 3 / KnowledgeChunk 26.

### 아직 실행하지 않은 것

- Streamlit UI 구동, Docker stack 구동, vLLM 호출, health check는 실행하지 않았다.
- Docker를 켜지 않았으므로 종료할 container도 없다.

## 2026-06-28 최종 Oracle 재검증

### 결과

- 최신 blocker 보완 후 Oracle 재검증에서 `<promise>VERIFIED</promise>`를 다시 받았다.
- Oracle은 자연어 paraphrase 최종 추리 수락, 오답 가설 기반 관련 NPC/퀘스트 되돌림, 현재 턴에서 마지막 pre-final 퀘스트가 준비 상태가 되는 즉시 로완으로 route하는 세 가지 직전 blocker가 구현과 회귀 테스트로 해결됐다고 판정했다.

### 최종 상태

- MVP 단계 기준 자동 퀘스트 진행, 로완 최종 라우팅, 정답/부분정답 분기, Admin 유지, LangGraph checkpoint continuity, answer-sensitive gate가 구현 완료 상태다.
- Docker/Streamlit/vLLM smoke test는 다음 신뢰도 강화 단계로 남겨 두며, 이번 작업에서는 Docker stack을 켜지 않았다.

## 2026-06-28 Docker QA 보고

### 개발 서버 조건

- Windows 개발 PC의 16GB VRAM 조건을 기준으로 `compose.design-test.yaml`과 `.env.design-test.example`를 사용했다.
- 운영 기본 E4B가 아니라 개발용 `google/gemma-4-E2B-it`를 사용했다.
- Compose 렌더링에서 Streamlit `MODEL_NAME=google/gemma-4-E2B-it`, vLLM `--served-model-name google/gemma-4-E2B-it`, `--gpu-memory-utilization 0.82`, `--max-model-len 3072`, localhost 포트 `18501/17474/17687/18000`을 확인했다.

### 실행한 Docker QA

- `docker compose --env-file .env.design-test.example -f compose.design-test.yaml --profile gpu config`: PASS.
- `docker compose --env-file .env.design-test.example -f compose.design-test.yaml --profile gpu up -d --build neo4j vllm streamlit`: PASS.
- `curl.exe -fsS http://127.0.0.1:18501/_stcore/health`: `ok`.
- `curl.exe -fsS http://127.0.0.1:18000/health`: PASS.
- `curl.exe -fsS http://127.0.0.1:18000/v1/models`: `google/gemma-4-E2B-it`, `max_model_len=3072` 확인.
- `docker compose ... run --rm streamlit uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --database neo4j`: PASS, NPC 4 / Location 8 / Quest 5 / Role 4 / Event 5 / Clue 8 / Truth 3 / KnowledgeChunk 26.
- Playwright 브라우저 QA: 메인 `persona_chat`, sidebar `NPC` / `Quest` / `Player Role`, 채팅 1턴, Admin `Memory Admin` / `Quest Admin` / `Concept Story Admin` 확인.
- vLLM 로그에서 `/v1/chat/completions` 200 OK를 확인했다.

### QA 중 발견 및 수정

- 첫 Admin 브라우저 QA에서 `src/streamlit/pages/admin.py`의 Concept Story selectbox가 `[''] + QUEST_OPTIONS`, `[''] + NPC_OPTIONS`로 tuple/list 결합을 시도해 `TypeError: can only concatenate list (not "tuple") to list`가 발생했다.
- `['', *QUEST_OPTIONS]`, `['', *NPC_OPTIONS]`로 수정했다.
- `tests/test_quest_auto_progression.py`에 해당 list+tuple concat 패턴이 다시 들어오지 않도록 source regression을 추가했다.
- 수정 후 `uv run --frozen python -m unittest discover -s tests -p "test_*.py"`: PASS, 14 tests.
- 수정 후 `uv run --frozen python -m compileall src/streamlit tests`: PASS.
- Streamlit 이미지를 재빌드/재기동한 뒤 Playwright 브라우저 QA를 재실행했고, Admin TypeError는 재현되지 않았다.

### Teardown

- QA 종료 후 `docker compose --env-file .env.design-test.example -f compose.design-test.yaml --profile gpu down`을 실행했다.
- `docker compose ... ps`: 실행 중 container 없음.
- `docker ps --filter "name=hazel_design_test" --format "{{.Names}} {{.Status}}"`: 출력 없음.
- `down -v`, `docker volume rm`, Neo4j reset은 실행하지 않았다.

### 남은 참고 사항

- Playwright console에서 정적 리소스 404 두 건이 보였지만 page error는 없었고 메인/채팅/Admin 흐름은 정상 통과했다.
- vLLM 첫 추론에서 Triton JIT latency warning이 있었지만 `/v1/chat/completions`는 200 OK로 완료됐다.

## 2026-06-28 단계형 NPC 대화 회귀 테스트 및 로그 정리

### 요청 반영 범위

- Docker 구동 없이 Python 테스트와 직접 런타임 호출만 사용했다.
- `rsc/data`와 `output` 산출물은 수정하지 않았다.
- 주요 코드 변경과 검증 결과를 이 문서에 기록했다.

### 추가한 회귀 계약

- `tests/test_quest_conversation_contract.py`를 추가해 단계형 질의 시나리오를 분리했다.
- NPC가 제공한 `player_observation` / `npc_hint` 문구 기반 메시지로 `run_quest_turn()`을 연속 호출하고, 활성 quest만 진행되며 아직 대화하지 않은 quest는 `in_progress`로 남는지 검증했다.
- 민민 부인에게 얻은 정보를 촌장 로완에게 공유하면 다음 필요 단서의 NPC/quest인 `patrol_leader_rio` / `q_pig_escape`로 유도되는지 검증했다.
- 최종 정답 문장을 알고 있어도 `q_changed_signpost`가 아직 `hint_1_given`이면 로완이 `solved`로 처리하지 않고 `patrol_leader_rio` / `q_changed_signpost`로 돌려보내는지 검증했다.
- 대화 로그 payload가 시스템 프롬프트, 모델명, vLLM URL, selection metadata 없이 `input`, `output`만 반환하는지 source-level로 검증했다.

### 코드 변경

- `src/streamlit/quest_rules.py`: 로완의 최종 정답 인정 직전에 모든 pre-final quest가 `ready_to_answer` 또는 `solved`인지 확인하는 gate를 추가했다. 미완료 quest가 있으면 정답 공개 없이 해당 quest의 NPC로 route한다.
- `src/streamlit/test_app.py`: `build_interaction_log()`가 `input`과 `output`만 반환하도록 줄였다. `append_feature_log()`의 timestamp 부여는 유지했다.
- `tests/test_quest_auto_progression.py`: 로완이 정답을 인정하는 기존 테스트에 pre-final quest readiness 전제 조건을 명시했다.

### RED/GREEN 증거

- RED: `uv run --frozen python -m unittest tests.test_quest_auto_progression`에서 의도한 2개 실패를 확인했다.
  - 로완이 pre-final quest 미완료 상태에서도 `solved`를 반환했다.
  - 대화 로그 builder가 `model`, `vllm_url`, `selection`, `input`, `output`을 반환했다.
- GREEN: 수정 후 `uv run --frozen python -m unittest tests.test_quest_auto_progression tests.test_quest_conversation_contract`는 18 tests OK.

### 비-Docker 검증

- `uv run --frozen python -m unittest discover -s tests -p "test_*.py"`: 18 tests OK.
- `uv run --frozen python -m compileall src/streamlit tests`: PASS.
- 직접 런타임 surface 확인:
  - 부분 정보 공유 시 로완 route: `('patrol_leader_rio', 'q_pig_escape')`.
  - 미완료 pre-final 상태에서 조기 정답 제시: `('ready_to_answer', 'patrol_leader_rio', 'q_changed_signpost', ())`.
  - chat interaction log keys: `['input', 'output']`.
- `basedpyright`는 현재 `uv run --frozen basedpyright ...`에서 실행 파일이 없어 실행하지 못했다.

### Oracle 검증 후 보강

- Ultrawork loop Oracle 검증에서 첫 완료 선언은 `NOT VERIFIED`를 받았다.
- 지적된 누락은 4개 pre-final quest 전체를 하나의 연속 대화로 진행하는 테스트 부족, 촌장 중간 공유 route 반복 검증 부족, 실제 JSONL 대화 로그가 timestamp 없이 질문/답변만 쓰이는지 검증 부족이었다.
- `tests/test_quest_conversation_contract.py`에 연속 대화 contract를 보강했다.
  - `q_glowing_mushroom`, `q_pig_escape`, `q_jelly_color`, `q_changed_signpost`를 순차 진행한다.
  - 중간마다 로완에게 공유해 다음 route가 `q_pig_escape`, `q_jelly_color`, `q_changed_signpost`로 이동하는지 확인한다.
  - 각 quest가 진행되기 전에는 `in_progress`로 남고, 마지막에는 네 pre-final quest 모두 `ready_to_answer`가 되는지 확인한다.
- `src/streamlit/chat_logging.py`를 추가해 대화 로그 builder/write path를 Streamlit import 없이 테스트 가능하게 분리했다.
- `src/streamlit/test_app.py`는 chat log 기록 시 `append_feature_log()`를 거치지 않고 `append_chat_interaction_log(CHAT_LOG_PATH, record)`를 사용한다. 따라서 chat JSONL에는 `timestamp_ms`, 시스템 프롬프트, 모델명, vLLM URL, selection metadata가 기록되지 않는다.
- 보강 후 검증:
  - `uv run --frozen python -m unittest tests.test_quest_conversation_contract`: 6 tests OK.
  - `uv run --frozen python -m unittest discover -s tests -p "test_*.py"`: 20 tests OK.
  - `uv run --frozen python -m compileall src/streamlit tests`: PASS.
  - 직접 surface 출력: routes `q_pig_escape -> q_jelly_color -> q_changed_signpost`, four pre-final states `ready_to_answer`, chat JSONL `{"input": "질문", "output": "답변"}`.
- Docker는 이 보강 과정에서도 실행하지 않았다.

### 아직 하지 않은 일

- Streamlit UI 구동, Docker stack 구동, vLLM 호출, health check는 아직 실행하지 않았다.
- Docker를 켜지 않았으므로 teardown 대상 container도 없다.

## 2026-06-28 테스트 스크립트 위치 이동

### 변경 내용

- 사용자 요청에 따라 자동 진행 회귀 테스트 파일을 `tests/`에서 `test_script/`로 이동했다.
- 이동한 파일:
  - `test_script/test_quest_auto_progression.py`
  - `test_script/test_quest_conversation_contract.py`
- 테스트 내부의 repository root 계산은 `Path(__file__).resolve().parents[1]` 구조라서 새 위치에서도 동일하게 project root를 가리킨다.

### 새 실행 명령

- 자동 진행 테스트 discovery 기준 명령은 `uv run --frozen python -m unittest discover -s test_script -p "test_quest_*.py"`이다.
- 직접 module 실행 기준 명령은 `uv run --frozen python -m unittest test_script.test_quest_auto_progression test_script.test_quest_conversation_contract`이다.
- compile 확인 기준 명령은 `uv run --frozen python -m compileall src/streamlit test_script/test_quest_auto_progression.py test_script/test_quest_conversation_contract.py`이다.
- `test_script/`에는 기존 legacy 테스트도 있어 전체 `test_*.py` discovery는 이번 이동 검증 범위 밖의 실패를 포함한다. `.gitignore`는 기존처럼 `test_script/` 대부분을 무시하되, 이동한 두 quest 테스트 파일만 추적 가능하도록 예외를 추가했다.
