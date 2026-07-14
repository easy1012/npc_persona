# NPC Persona Version 2 Scenario Contract

이 문서는 구현 기준이다. 단, 사용자 변경 지시에 따라 아래 시나리오의 테스트 작성/실행은 구현 완료 후 최종 승인 뒤에만 진행한다.

## SC-01 Non-Chief Clue Unlock

민민, 리오, 루미 중 현재 퀘스트의 담당 NPC에게 사용자가 다음 단계의 정황 근거를 제시하면, 해당 단계의 `unlocked_clue_ids`가 누적되고 quest state와 hint level이 상승한다. pass 조건은 반환 decision에 새 단서 ID가 포함되고, `answer_sensitive` truth 공개 상태가 열리지 않는 것이다.

## SC-02 Non-Chief Final Routing

비촌장 NPC에게 필수 단서가 모두 모인 뒤 최종 추리를 말하면, 퀘스트를 `solved`로 만들지 않고 `chief_rowan`에게 종합 추리를 말하라는 route decision을 반환한다. pass 조건은 `route_to_npc_id == "chief_rowan"`이고 최종 truth reveal flag가 false인 것이다.

## SC-03 Chief Correct Final Deduction

로완에게 필수 단서가 모두 모인 상태에서 올바른 연결 추리를 제시하면 quest state가 `solved`가 되고 전말 정리 응답을 허용한다. pass 조건은 `quest_state == "solved"`, `allowed_hint_level == 3`, reveal 대상 truth가 반환되는 것이다.

## SC-04 Chief Partial Or Wrong Deduction

로완에게 누락 또는 오답 추리를 제시하면 quest state는 `solved`가 되지 않고, 빠진 단서 또는 반증 단서와 관련된 NPC로 되돌린다. pass 조건은 missing/disproof clue ID와 `route_to_npc_id`가 반환되고 `quest_state != "solved"`인 것이다.

## SC-05 Checkpoint Continuity

같은 `thread_id`로 두 번 호출하면 두 번째 호출은 첫 번째 호출에서 획득한 NPC/퀘스트 단서를 기억한다. pass 조건은 두 번째 decision의 observed clue set이 첫 번째 clue set을 포함하는 것이다.

## SC-06 Checkpoint Isolation

서로 다른 NPC 또는 퀘스트 thread는 단서를 공유하지 않는다. pass 조건은 다른 thread에서 이전 thread의 clue ID가 observed set에 나타나지 않는 것이다.

## SC-07 Admin Preservation

`src/streamlit/pages/admin.py`는 Memory Admin, Quest Admin, Concept Story Admin을 유지한다. pass 조건은 수동 Quest Admin override가 여전히 `quest_state_by_quest`와 `allowed_hint_level_by_quest`를 갱신하는 것이다.

## SC-08 Retrieval Gate Preservation

자동 진행이 추가되어도 `get_allowed_chunks()`의 `hint_level <= allowed_hint_level` 및 `answer_sensitive` 공개 조건은 유지된다. pass 조건은 `ready_to_answer` 전에는 answer-sensitive chunk가 차단되고, `ready_to_answer` 이후에만 허용되는 것이다.

## SC-09 Docker Teardown

최종 승인 후 Docker QA를 실행했다면, 작업 종료 전에 compose stack을 종료한다. pass 조건은 teardown 명령 이후 해당 QA stack의 실행 컨테이너가 남아 있지 않는 것이다.

## 승인 전 금지 항목

- `python -m unittest ...`
- `py_compile` 등 테스트성 컴파일 확인
- `streamlit run`
- Docker `up`
- health endpoint 호출
- vLLM 모델 호출

위 항목은 구현 완료 보고 후 사용자가 최종 승인할 때만 실행한다.
