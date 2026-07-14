# NPC별 퀘스트 진행 질의응답 QA 로그

## 요약

- 실행일: 2026-06-30
- 실행 환경: `compose.design-test.yaml` + `.env.design-test.example`
- Streamlit: `http://127.0.0.1:18501`
- vLLM 모델: `google/gemma-4-E2B-it`
- Neo4j: `hazel_design_test`, `KnowledgeChunk` 30개
- 자동 품질 QA 결과: PASS, 11턴
- 원본 산출물: `output/reports/quest_scenario_quality_20260630.md`, `output/reports/quest_scenario_quality_20260630.json`
- 재현 스크립트: `test_script/run_quest_scenario_quality.py`

이번 검증의 핵심은 “각 NPC가 사용자의 자연스러운 추리 질의를 보고 자기 퀘스트 단계를 올바르게 진행시키며 추가 힌트를 제공하는가”, 그리고 “로완 촌장이 모든 선행 NPC 진행이 충분히 최종 단계에 도달했을 때만 전체 전말을 공개하는가”이다. `output/reports/quest_scenario_transcript_20260630.*`는 중간 실패 확인용 산출물이며, 최종 판정 기준은 더 강한 품질 gate를 통과한 `quest_scenario_quality_20260630.*`이다.

## 사전 환경 확인

- `docker ps --filter "name=hazel_design_test"`에서 Neo4j, vLLM, Streamlit 컨테이너가 모두 healthy였다.
- Streamlit health endpoint `http://127.0.0.1:18501/_stcore/health`는 `ok`를 반환했다.
- vLLM `/v1/models`는 `google/gemma-4-E2B-it`만 반환했다.
- Neo4j `KnowledgeChunk` 총합은 30개였다.
- NPC별 chunk 분포는 `chief_rowan: 8`, `mage_lumi: 6`, `minmin_lady: 9`, `patrol_leader_rio: 7`이었다.

## NPC별 질의응답 로그

### 1. 민민 부인 - 반짝이는 버섯 첫 단서

- NPC: `minmin_lady`
- 퀘스트: `q_glowing_mushroom`
- 사용자 질의: 밤에만 눈에 띄는 빛과 주변 가루를 본다. 낮과 밤을 나누어 보렴.
- 진행 판정: `hint_1_given`
- 새 단서: `clue_bright_mushroom`
- 남은 단서: `clue_moonlit_night`
- 정답 민감 chunk 노출: 없음
- NPC 답변:

> 아이고, 우리 모험가. 밤에만 빛이 강하게 보인다고? 그건 참 신기한 일이란다. 내가 예전에 속삭임 숲 입구에서 봤을 때도 그랬지. 낮에는 그저 평범한 버섯일 뿐인데, 달이 밝은 밤이 되면 마치 작은 등불처럼 눈에 띄는 모양이었단다. 그 주변에 희미한 가루 같은 것이 남는다고 했지. 낮과 밤을 잘 나누어 보면서 그 빛이 언제 가장 강한지 한번 유심히 살펴보렴.

- 판정: PASS. 버섯, 빛, 밤, 가루를 자연스럽게 언급했고 최종 전말은 말하지 않았다.

### 2. 민민 부인 - 달 밝은 밤 단서 완료

- NPC: `minmin_lady`
- 퀘스트: `q_glowing_mushroom`
- 사용자 질의: 민민 부인의 기억이 달 밝은 밤에 집중된다. 달이 밝으면 더 보였단다.
- 진행 판정: `ready_to_answer`
- 누적 단서: `clue_bright_mushroom`, `clue_moonlit_night`
- 남은 단서: 없음
- 정답 민감 chunk 노출: 없음
- NPC 답변:

> 아이고, 우리 모험가, 달 밝은 밤에 몽실버섯이 더 눈에 띄었다고? 내가 예전에 봤을 때도 그랬지 뭐니. 그게 밤에만 피어나는 거라는데, 달빛이 환할 때면 그 빛이 더 강하게 느껴지는 것 같더라. 혹시 그 주변에 뭔가 가루 같은 것이 남는다는 것도 기억하렴. 그게 다음 힌트가 될지도 모르지.

- 판정: PASS. 민민 부인의 퀘스트는 최종 답변 준비 상태까지 진행됐다.

### 3. 순찰대장 리오 - 말랑돼지 발자국 첫 단서

- NPC: `patrol_leader_rio`
- 퀘스트: `q_pig_escape`
- 사용자 질의: 말랑돼지 발자국이 숲 입구 쪽으로 이어진다. 방향을 봐라.
- 진행 판정: `hint_1_given`
- 새 단서: `clue_pig_tracks`
- 남은 단서: `clue_glittering_powder`
- 정답 민감 chunk 노출: 없음
- NPC 답변:

> 확인했다. 말랑돼지 발자국이 숲 입구 방향으로 이어진다는 증거는 기록에 남아있다. **방향을 봐라.** 그 발자국을 따라가면 다음 단서를 찾을 수 있을 것이다. 초보자는 방심해서는 안 된다.

- 판정: PASS. 발자국과 숲 방향을 물리 증거로 제시했다.

### 4. 순찰대장 리오 - 반짝이는 가루 단서 완료

- NPC: `patrol_leader_rio`
- 퀘스트: `q_pig_escape`
- 사용자 질의: 가루가 발자국 주변에서 발견된다. 정체는 몰라도 같은 현장에 있다.
- 진행 판정: `ready_to_answer`
- 누적 단서: `clue_pig_tracks`, `clue_glittering_powder`
- 남은 단서: 없음
- 정답 민감 chunk 노출: 없음
- NPC 답변:

> 반짝이는 가루가 발자국 주변에서 발견된다고? 확인했다. 그 가루의 정체는 아직 불분명하지만, 말랑돼지들이 움직인 방향과 관련이 있을 가능성이 높다. 기록에 따르면, 말랑돼지들은 특정 방향으로 움직였다. 그 방향을 따라 더 조사해라.

- 판정: PASS. 리오의 말랑돼지 퀘스트는 최종 답변 준비 상태까지 진행됐다.

### 5. 순찰대장 리오 - 방울젤리 색 변화 관찰

- NPC: `patrol_leader_rio`
- 퀘스트: `q_jelly_color`
- 사용자 질의: 평소보다 진한 색을 띠는 방울젤리 개체가 보인다. 가까이 가되 방심하지 마라.
- 진행 판정: `hint_2_given`
- 새 단서: `clue_jelly_color_change`
- 남은 단서: `clue_mana_reaction`
- 정답 민감 chunk 노출: 없음
- NPC 답변:

> 방울젤리의 색 변화를 확인했다. 이는 분명히 주의해야 할 징후다. 가까이 접근하되, 어떤 움직임이나 이상 징후도 놓치지 마라. 내가 관찰한 증거는 이렇다. 다음으로, 그 개체가 보이는 장소 주변의 지형이나 주변 환경에 파손 흔적이나 다른 단서가 있는지 확인해라.

- 판정: PASS. 색 변화는 열렸고, 마나 반응은 아직 루미 쪽 추가 확인으로 남았다.

### 6. 마법사 루미 - 마나 반응 단서 완료

- NPC: `mage_lumi`
- 퀘스트: `q_jelly_color`
- 사용자 질의: 루미의 도구가 약한 반응을 보인다. 결정적 답은 아니지만 흐름은 있어.
- 진행 판정: `ready_to_answer`
- 누적 단서: `clue_jelly_color_change`, `clue_mana_reaction`
- 남은 단서: 없음
- 정답 민감 chunk 노출: 없음
- NPC 답변:

> 음, 루미의 도구가 약한 반응을 보인다고? 흥미롭네! 마법의 흐름이 아주 미묘하게 반응하고 있다는 신호일지도 몰라. 혹시 그 도구가 어떤 종류의 마나에 반응하는지 한번 생각해 봤어? 방울젤리처럼 환경 변화에 민감한 것들이 주변 마나의 흐름을 알려주는 경우가 있거든.

- 판정: PASS. 루미는 마나 반응을 가설 수준으로 설명했고, 최종 전말은 공개하지 않았다.

### 7. 순찰대장 리오 - 표지판 변화 첫 단서

- NPC: `patrol_leader_rio`
- 퀘스트: `q_changed_signpost`
- 사용자 질의: 표지판 방향이 평소와 다르다. 표지판만 보지 말고 주변을 봐라.
- 진행 판정: `hint_1_given`
- 새 단서: `clue_changed_signpost`
- 남은 단서: `clue_root_marks`
- 정답 민감 chunk 노출: 없음
- NPC 답변:

> 흠. 표지판 방향이 다르다고 해서 성급하게 움직여서는 안 된다. 나는 소문이 아닌, 눈에 보이는 증거와 기록을 신뢰한다. 주변을 주의 깊게 관찰하고, 표지판 외에 다른 파손 흔적이나 이동 방향의 단서를 찾아라. 그것이 우리가 나아가야 할 방향을 알려줄 것이다.

- 판정: PASS. 표지판 변화는 열렸고, 주변 물리 흔적 확인이 다음 단계로 남았다.

### 8. 민민 부인 - 표지판 관련 소문 보조 확인

- NPC: `minmin_lady`
- 퀘스트: `q_changed_signpost`
- 사용자 질의: 장난기 많은 숲속 생물 이야기를 듣지만 확정하지 않는다.
- 진행 판정: `hint_1_given` 유지
- 남은 단서: `clue_root_marks`
- 정답 민감 chunk 노출: 없음
- NPC 답변:

> 아이고, 그 꼬마그루터기 이야기는 마을 사람들 사이에서만 떠도는 소문이란다. 내가 직접 표지판을 누가 바꿨는지 본 적은 없지 뭐니. 하지만 숲 입구 주변을 한번 잘 살펴보고, 리오에게도 물어보렴. 숲속에서 무슨 일이 벌어지는지 직접 눈으로 확인해야 알 수 있을 거란다.

- 판정: PASS. 민민 부인은 소문과 직접 목격을 구분했고, 리오 확인을 자연스럽게 유도했다.

### 9. 순찰대장 리오 - 뿌리 자국 단서 완료 및 로완 유도

- NPC: `patrol_leader_rio`
- 퀘스트: `q_changed_signpost`
- 사용자 질의: 사람 발자국 대신 뿌리 자국과 나뭇조각이 보인다. 사람이 한 흔적은 아니다.
- 진행 판정: `ready_to_answer`
- 누적 단서: `clue_changed_signpost`, `clue_root_marks`
- route: `chief_rowan` / `q_main_spore_night`
- 정답 민감 chunk 노출: 없음
- NPC 답변:

> 음. 내가 관찰한 증거는 사람의 발자국이 아닌, 뿌리가 끌린 듯한 자국과 작은 나뭇조각이 남아 있다는 사실이다. **소문보다 발자국, 파손 흔적, 이동 방향 같은 물리적 단서를 더 신뢰한다.** 플레이어는 현장 간격과 파편 방향을 먼저 비교하여 확인해야 한다.

- 판정: PASS. 네 번째 선행 퀘스트도 최종 답변 준비 상태가 되었고, 리오는 최종 전말을 확정하지 않고 로완에게 종합 추리를 유도했다.

## 로완 촌장 검증

### 10. 로완 - 단서 미완료 상태의 조기 최종 추리 차단

- NPC: `chief_rowan`
- 퀘스트: `q_main_spore_night`
- 사용자 질의: 버섯 빛, 돼지 발자국, 젤리 색, 표지판 변화, 반짝이는 가루를 합치면 밤의 마나와 포자가 원인인 것 같아요. 이게 최종 답인가요?
- 진행 판정: `ready_to_answer`
- route: `patrol_leader_rio` / `q_changed_signpost`
- 누락 단서: `clue_root_marks`
- 공개 truth: 없음
- 정답 민감 chunk 노출: 없음
- NPC 답변:

> 음... 당신의 추론은 흥미롭습니다. 하지만 아직은 충분하지 않습니다. 순찰대장 리오에게서 받은 정보 중, **순찰대장 리오에게 바뀐 숲길 표지판의 남은 단서인 뿌리 자국과 나뭇조각 확인이 부족합니다. 표지판 주변의 뿌리 자국과 나뭇조각을 다시 확인해야 합니다.** 이 단서들을 먼저 점검해 보십시오.

- 판정: PASS. 로완은 정답을 인정하지 않았고, `clue_root_marks` 누락 때문에 순찰대장 리오의 `q_changed_signpost`로 명시적으로 되돌렸다. 이 단계에서는 answer-sensitive chunk와 최종 truth가 노출되지 않았다.

### 11. 로완 - 모든 선행 NPC 단계 완료 후 최종 전말 공개

- NPC: `chief_rowan`
- 퀘스트: `q_main_spore_night`
- 사용자 질의: 민민의 달 밝은 밤과 강한 버섯 빛, 리오의 숲 방향 발자국과 가루, 루미의 방울젤리 마나 반응, 표지판 주변의 뿌리 자국까지 모두 합치면 달빛 샘터의 마나 주기 강화가 포자와 생물 반응을 일으킨 것이 정답 아닌가요?
- 진행 판정: `solved`
- 공개 truth: `truth_moonwell_mana_cycle`
- 정답 민감 chunk 노출: `rowan_chronicle_005`, `rowan_chronicle_006`, `rowan_chronicle_007`, `rowan_chronicle_001`
- NPC 답변:

> 음... 당신의 추론이 꽤나 논리적으로 연결되어 있군요. 민민 부인의 달 밝은 밤과 버섯 빛, 리오의 숲 방향 발자국과 가루, 그리고 루미의 방울젤리 마나 반응과 표지판 주변의 뿌리 자국까지 모두 종합해 볼 때, 달빛 샘터의 마나 주기 강화가 포자와 생물 반응을 일으킨 것이 맞습니다. 민민 부인, 순찰대장 리오, 마도사 루미의 보고가 달빛 샘터의 마나 주기 강화로 이어진다는 것이 사실입니다. 이로써 이 사건은 해결되었습니다.

- 판정: PASS. 모든 선행 NPC 진행 단계가 최종 준비 상태가 된 뒤에만 로완이 `solved`로 전환했고, 달빛 샘터의 마나 주기 강화 전말과 단서 연결을 종합해 말했다.

## Streamlit Admin 단계 진행 검증

- 검증 도구: `streamlit.testing.v1.AppTest`
- 렌더링 결과: 예외 0개
- 확인 탭: `Memory Admin`, `Quest Admin`, `Concept Story Admin`
- 확인 컨트롤: `Quest`, `Quest State`, `Save Quest State`, `Allowed Hint Level`
- 전체 상태 저장 검증: 5개 퀘스트 x 6개 상태 = 30개 조합
- 검증 동작:
  - 각 퀘스트를 `not_started`, `in_progress`, `hint_1_given`, `hint_2_given`, `ready_to_answer`, `solved`로 순차 선택했다.
  - 각 상태에서 `Save Quest State`를 클릭했다.
  - session state의 `quest_state_by_quest`가 선택 상태로 저장되는지 확인했다.
  - `allowed_hint_level_by_quest`가 `QUEST_STATE_HINT_LEVELS`와 동일한 값으로 저장되는지 확인했다.
  - 첫 검증 조합은 `q_glowing_mushroom / not_started / hint level 0`, 마지막 검증 조합은 `q_main_spore_night / solved / hint level 3`이었다.

## 최종 결론

- 민민 부인, 순찰대장 리오, 마법사 루미는 각자 자기 지식 범위 안에서 단계별 단서를 제공했고, 최종 전말은 공개하지 않았다.
- 리오는 네 번째 선행 퀘스트까지 완료되면 로완에게 종합 추리를 제시하도록 유도했다.
- 로완은 단서가 하나라도 부족한 경우 최종 정답을 인정하지 않고 미완료 NPC/퀘스트로 되돌렸다.
- 로완은 모든 선행 NPC 진행 단계가 최종 준비 상태가 되고, 사용자가 전체 정답을 종합해 제시했을 때만 `truth_moonwell_mana_cycle`과 전체 전말을 공개했다.
- Streamlit Admin 화면에서도 퀘스트 상태 선택과 저장에 따라 hint level이 정상 반영됐다.

따라서 이번 자연 질의 기반 NPC별 퀘스트 진행, Admin 단계 진행, 로완 partial/final 분기 검증은 PASS다.
