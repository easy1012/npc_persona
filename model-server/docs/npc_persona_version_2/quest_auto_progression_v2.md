# NPC Persona Version 2 Quest Auto-Progression Design

## 목적

Version 2는 현재 수동 Quest Admin 중심의 퀘스트 진행을 대화 기반 자동 진행으로 확장한다. 사용자가 NPC와 대화하며 얻은 힌트와 정황 근거를 다시 제시하면 퀘스트 단계가 진행되고, 필요한 다음 힌트가 열리며, 모든 NPC별 단서가 최종 단계에 도달하면 촌장 로완에게 종합 추리를 제시하도록 유도한다.

## 범위

- 유지: `src/streamlit/pages/admin.py`의 Memory Admin, Quest Admin, Concept Story Admin.
- 유지: 기존 `quest_state_by_quest`와 `allowed_hint_level_by_quest`를 조회 권한의 최종 상태 저장소로 사용.
- 유지: `get_allowed_chunks()`의 `hint_level` 및 `answer_sensitive` 필터.
- 추가: LangGraph `StateGraph` 기반 퀘스트 진행 그래프와 체크포인트.
- 추가: NPC별/퀘스트별 대화 기억과 획득 단서 상태를 그래프 상태로 누적.
- 추가: 비촌장 NPC의 최종 추론 단계에서는 로완에게 가도록 유도.
- 추가: 로완은 정답이면 전말을 정리하고, 부족하거나 틀린 추리면 관련 NPC와 단서로 되돌린다.

## 소스 오브 트루스

| 데이터 | 위치 | 사용 방식 |
|---|---|---|
| 퀘스트 단계 | `rsc/data/quests/*.yaml` `story_expansion.quest_steps` | 단계 순서, 담당 NPC, 해금 단서, 다음 조건 |
| 필수 단서 | `required_clue_ids` | `ready_to_answer` 및 최종 판정 조건 |
| 오답 가설 | `wrong_hypotheses` | 부분 실패/리다이렉트 근거 |
| 정답 공개 정책 | `answer_reveal_policy` | 로완만 최종 truth 공개 가능 |
| 단서 메타 | `rsc/data/world/clues.yaml` | 단서명, 힌트 레벨, 관련 truth |
| truth 메타 | `rsc/data/world/truths.yaml` | 최종 공개 조건 |

`output/`은 재생성 산출물이므로 자동 진행 규칙의 입력으로 사용하지 않는다.

## LangGraph 설계

LangGraph는 대화 1턴마다 다음 순서로 동작한다.

1. `load_checkpoint`: thread state에서 현재 NPC/퀘스트의 누적 단서와 진행 상태를 복원한다.
2. `evaluate_deduction`: 사용자 메시지와 최근 NPC 응답을 현재 퀘스트 단계, 단서명, truth명, 오답 가설과 대조한다.
3. `advance_or_route`: 충족된 단서를 누적하고 quest state와 hint level을 계산한다.
4. `chief_review`: `chief_rowan`일 때만 최종 정답/부분 정답/오답을 판정한다.
5. `emit_decision`: Streamlit이 적용할 결정값을 반환한다.

MVP 체크포인터는 테스트/개발 친화적인 `InMemorySaver`를 사용한다. 공식 문서상 체크포인터는 thread별 graph state snapshot을 저장하며, 호출 시 `config={"configurable": {"thread_id": ...}}`가 필요하다. 노드는 체크포인트 재실행에 대비해 같은 입력을 여러 번 처리해도 단서가 중복되지 않도록 idempotent하게 작성한다.

## Thread ID 규칙

```text
session:{session_id}:npc:{npc_id}:quest:{quest_id}
```

Streamlit 세션에서 생성한 `session_id`를 기준으로 NPC/퀘스트별 체크포인트를 분리한다. 이 규칙은 한 NPC의 단서가 다른 NPC/퀘스트에 섞이는 것을 막는다.

## 퀘스트 상태 전이

| 조건 | 상태 | 힌트 레벨 |
|---|---|---|
| 획득 단서 없음 | `in_progress` | 1 |
| hint level 1 단서 획득 | `hint_1_given` | 1 |
| hint level 2 단서 획득 | `hint_2_given` | 2 |
| 필수 단서 모두 획득 | `ready_to_answer` | 3 |
| 로완이 최종 추리를 정답으로 판정 | `solved` | 3 |

`not_started`는 Admin 수동 설정으로 유지할 수 있지만, 대화가 시작되어 단서가 감지되면 `in_progress` 이상의 상태로 이동한다.

## NPC별 라우팅

- 민민, 리오, 루미는 자신이 아는 단서와 단계 힌트만 제공한다.
- 비촌장 NPC가 필수 단서가 모두 모인 상태에서 최종 원인을 묻거나 추리하면 로완에게 종합 보고하라고 안내한다.
- 로완은 필수 단서가 모두 모인 뒤에만 최종 truth 연결을 검토한다.
- 로완이 추리에서 누락된 단서를 발견하면 해당 단서와 관련된 NPC 또는 quest step으로 되돌린다.

## Streamlit 통합

대화 처리 후 다음 값을 업데이트한다.

- `st.session_state.quest_state_by_quest[quest_id]`
- `st.session_state.allowed_hint_level_by_quest[quest_id]`
- 현재 선택 퀘스트와 일치할 때 `quest_state`, `allowed_hint_level`
- `last_debug`에 quest decision 요약
- NPC별 memory에는 기존처럼 사용자/응답 턴을 유지

Admin 페이지는 별도 관리자 도구로 유지한다. Quest Admin이 저장한 수동 값은 계속 현재 session state에 반영되며, 자동 진행은 같은 state map을 갱신하는 추가 경로로만 동작한다.

## 테스트 승인 게이트

사용자 변경 지시에 따라 테스트 작성, 테스트 실행, Streamlit 구동 테스트, Docker 구동 테스트, health check는 구현 완료 후 사용자 최종 승인을 받은 뒤에만 진행한다. 승인 전에는 문서, 구현, 설정 문서 작성만 수행한다.

## Docker 및 로컬 모델 정책

- 운영 기본 모델: `google/gemma-4-E4B-it`.
- 개발용 Windows PC QA 모델: `google/gemma-4-E2B-it`.
- 16GB VRAM 환경에서는 E2B용 compose/env 예시를 별도로 두고, 낮은 `max-model-len`과 보수적인 GPU memory utilization을 사용한다.
- 승인 후 Docker QA를 실행했다면 모든 작업 종료 전에 반드시 `docker compose ... down`으로 종료해 VRAM을 회수한다.
