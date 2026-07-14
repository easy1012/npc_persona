# NPC별 퀘스트 진행 재현 가이드

이 문서는 `hazel_design_test` 개발 스택에서 검증한 NPC별 자연 질의 시나리오를 사용자가 직접 재현하기 위한 안내서다. 기준 QA 산출물은 `output/reports/quest_scenario_quality_20260714.md`이며, 모델은 개발용 `google/gemma-4-E2B-it`이다.

## 실행 전 조건

- 개발용 Compose 파일은 `compose.design-test.yaml`을 사용한다.
- 환경 파일은 운영 `.env`가 아니라 `.env.design-test.example`을 명시한다.
- 운영 기본 모델 `google/gemma-4-E4B-it`를 받거나 설정하지 않는다.
- Neo4j reset, Docker volume 삭제, 운영 DB 변경은 하지 않는다.
- Streamlit 접속 주소는 `http://127.0.0.1:18501`이다.

## 재현 순서

1. Streamlit 메인 페이지에서 NPC, Quest, Player Role이 선택된 상태인지 확인한다.
2. 아래 표의 순서대로 NPC와 Quest를 맞추고 질문을 입력한다.
3. 각 턴 뒤 sidebar의 debug/runtime 정보나 QA 로그에서 `quest_state`, `route_to_npc_id`, `route_to_quest_id`, `reveal_truth_ids`를 확인한다.
4. `ready_to_answer` 전에는 `answer_sensitive` chunk가 노출되지 않아야 한다.
5. 로완 최종 단계에서만 `truth_moonwell_mana_cycle` 공개가 허용된다.

## NPC별 입력과 기대 결과

| 순서 | NPC / Quest | 입력 예시 | 기대 상태 | 기대 응답 품질 |
|---|---|---|---|---|
| 1 | 민민 부인 / `q_glowing_mushroom` | `안녕하세요. 건강하신가요?` | `in_progress`, 새 단서 없음 | 일반 인사만으로 힌트 단계가 오르지 않는다. |
| 2 | 민민 부인 / `q_glowing_mushroom` | `밤에만 눈에 띄는 빛과 주변 가루를 본다. 낮과 밤을 나누어 보렴.` | `hint_1_given`, missing `clue_moonlit_night` | 버섯의 빛, 밤, 주변 가루를 말하되 최종 원인은 말하지 않는다. |
| 3 | 민민 부인 / `q_glowing_mushroom` | `민민 부인의 기억이 달 밝은 밤에 집중된다. 달이 밝으면 더 보였단다.` | `ready_to_answer` | 달 밝은 밤과 몽실버섯 빛을 연결하고 다음 조사로 자연스럽게 넘긴다. |
| 4 | 순찰대장 리오 / `q_pig_escape` | `안녕하세요. 건강하신가요?` | `in_progress`, 새 단서 없음 | 일반 인사와 조사 근거를 구분한다. |
| 5 | 순찰대장 리오 / `q_pig_escape` | `말랑돼지 발자국이 숲 입구 쪽으로 이어진다. 방향을 봐라.` | `hint_1_given`, missing `clue_glittering_powder` | 발자국, 숲 방향, 흔적 추적을 강조한다. |
| 6 | 순찰대장 리오 / `q_pig_escape` | `가루가 발자국 주변에서 발견된다. 정체는 몰라도 같은 현장에 있다.` | `ready_to_answer` | 반짝이는 가루와 발자국의 관계를 말하지만 최종 전말은 확정하지 않는다. |
| 7 | 순찰대장 리오 / `q_jelly_color` | `평소보다 진한 색을 띠는 방울젤리 개체가 보인다. 가까이 가되 방심하지 마라.` | `hint_2_given`, missing `clue_mana_reaction` | 방울젤리 색 변화와 추가 관찰 필요성을 말한다. |
| 8 | 마법사 루미 / `q_jelly_color` | `안녕하세요. 차를 한 잔 마셔도 될까요?` | `hint_2_given` 유지, 새 단서 없음 | 앞선 조사 단계는 유지하되 근거 없는 승격은 하지 않는다. |
| 9 | 마법사 루미 / `q_jelly_color` | `루미의 도구가 약한 반응을 보인다. 결정적 답은 아니지만 흐름은 있어.` | `ready_to_answer` | 마나 반응과 흐름을 가설 수준으로 말한다. |
| 10 | 순찰대장 리오 / `q_changed_signpost` | `표지판 방향이 평소와 다르다. 표지판만 보지 말고 주변을 봐라.` | `hint_1_given`, missing `clue_root_marks` | 표지판 방향, 주변 흔적, 경로 확인을 유도한다. |
| 11 | 민민 부인 / `q_changed_signpost` | `장난기 많은 숲속 생물 이야기를 듣지만 확정하지 않는다.` | `hint_1_given` 유지 | 소문과 직접 목격을 구분하고 숲 입구 주변 확인 또는 리오 확인을 권한다. |
| 12 | 순찰대장 리오 / `q_changed_signpost` | `사람 발자국 대신 뿌리 자국과 나뭇조각이 보인다. 사람이 한 흔적은 아니다.` | `ready_to_answer`, route `chief_rowan` / `q_main_spore_night` | 뿌리 자국과 나뭇조각을 물리 증거로 정리하고 로완에게 종합 추리를 안내한다. |
| 13 | 헤이즐 촌장 로완 / `q_main_spore_night` | `버섯 빛, 돼지 발자국, 젤리 색, 표지판 변화, 반짝이는 가루를 합치면 밤의 마나와 포자가 원인인 것 같아요. 이게 최종 답인가요?` | `ready_to_answer`, route `patrol_leader_rio` / `q_changed_signpost`, missing `clue_root_marks` | 최종 정답을 인정하지 않고 순찰대장 리오에게 표지판 주변 남은 단서를 확인하게 유도한다. |
| 14 | 헤이즐 촌장 로완 / `q_main_spore_night` | `민민의 달 밝은 밤과 강한 버섯 빛, 리오의 숲 방향 발자국과 가루, 루미의 방울젤리 마나 반응, 표지판 주변의 뿌리 자국까지 모두 합치면 달빛 샘터의 마나 주기 강화가 포자와 생물 반응을 일으킨 것이 정답 아닌가요?` | `solved`, reveal `truth_moonwell_mana_cycle` | 첫 문장부터 추론이 맞다고 인정하고 달빛 샘터, 마나 주기, 포자, 리오/루미/민민/표지판 단서를 함께 연결한다. |

## 통과 기준

- 각 비촌장 NPC는 자기 단서와 다음 조사 방향만 말하고 최종 전말을 공개하지 않는다.
- 로완 partial 턴은 `clue_root_marks` 누락을 이유로 `patrol_leader_rio`와 `q_changed_signpost`로 되돌린다.
- 로완 final 턴은 모든 선행 퀘스트가 준비된 뒤에만 `solved`가 되고 `truth_moonwell_mana_cycle`을 공개한다.
- 최종 QA 기준에서는 14개 턴 모두 응답 존재뿐 아니라 핵심 단어 조합 품질을 만족해야 한다.

## 확인 명령

아래 명령은 같은 시나리오를 자동 품질 QA로 재실행한다.

```powershell
$env:PYTHONPATH="."
uv run --frozen python -m test_script.run_quest_scenario_quality
```

기대 출력은 `PASS quality QA records=14`이며, 보고서는 `output/reports/quest_scenario_quality_20260714.md`와 `output/reports/quest_scenario_quality_20260714.json`에 기록된다.
