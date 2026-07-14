# DB 및 데이터 증강 기록

## 2026-06-29 작업 시작 기록

### 무엇을

- 연속대화 QA 중 확인할 DB/데이터 검증 범위를 정했다.
- 아직 canonical story data, Neo4j live data, import logic은 수정하지 않았다.

### 왜

- NPC별 지식 제한이 맞게 적용되는지 확인해야 한다.
- 특히 순찰대장 리오가 말투만 강하고 유용한 물리 증거를 충분히 제공하지 못하는 경우, 기존 퀘스트/NPC 범위 안에서만 데이터를 증강해야 한다.

### 누가

- 작업자: Sisyphus.
- 승인자: 사용자.

### 언제

- 2026-06-29 작업 시작 시점.

### 어디서

- canonical source: `rsc/data/`.
- live DB 검증 대상: `compose.design-test.yaml`의 `hazel_design_test` Neo4j.
- 기록 위치: `docs/npc_persona_version_2/db_data_augmentation_log.md`.

### 어떻게

- `rsc/data`를 source of truth로 유지한다.
- Neo4j는 reset 없이 merge import와 Cypher 조회/필요 시 merge 수정만 사용한다.
- MapleStory 조사는 현재 프로젝트의 기존 퀘스트와 NPC에 관련된 정보만 사용하며, 새 NPC나 새 퀘스트는 추가하지 않는다.

## 2026-06-29 q_jelly_color 루미 지식 노출 보정

### 무엇을

- `rsc/data/npcs/mage_lumi.md`의 `lumi_chronicle_004`를 보정했다.
- 기존 hint-2 비정답 chunk가 `달빛 샘터의 마나가 강해졌을 가능성`을 직접 말해, `answer_sensitive=false` 상태에서도 최종 원인에 가까운 표현이 모델 응답에 노출됐다.
- 표현을 `숲 입구 가까운 곳`, `같은 방향의 흐름에 반응했을 가능성`으로 낮춰 루미가 가설만 말하도록 조정했다.

### 왜

- 브라우저 QA에서 루미가 `q_jelly_color` hint 단계에서 “달빛 샘터 쪽 마나가 강해졌을 가능성”을 직접 언급했다.
- 루미는 최종 원인을 확정하는 NPC가 아니며, `answer_reveal_allowed=false` 상태에서는 로완 전용 종합 결론을 열면 안 된다.

### 누가

- 작업자: Sisyphus.
- 승인자: 사용자.

### 언제

- 2026-06-29 live Docker 대화 QA 중 루미 응답을 확인한 직후.

### 어디서

- canonical source: `rsc/data/npcs/mage_lumi.md`.
- live DB 반영: `hazel_design_test` Neo4j에 reset 없이 source importer merge 실행.
- 관찰 로그: `output/reports/streamlit_retrieval_events.jsonl`, `output/reports/streamlit_llm_interactions.jsonl`.

### 어떻게

- 원천 Markdown chunk를 수정한 뒤 dry-run import로 NPC 4, Location 8, Quest 5, Role 4, Event 5, Clue 8, Truth 3, KnowledgeChunk 26 구조가 유지되는지 확인했다.
- Docker Streamlit 이미지를 rebuild/recreate하고 `src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --database neo4j`를 `--reset` 없이 다시 실행했다.
- 재검증에서 최신 retrieval의 `lumi_chronicle_004`가 “같은 방향의 흐름” 가설만 제공하고, UI 응답도 “숲 입구 근처”, “같은 방향의 마나 흐름” 수준으로 제한되는 것을 확인했다.

## 2026-06-29 MapleStory 관련 조사 기록

### 무엇을

- 기존 퀘스트와 NPC에 관련된 MapleStory 참고 사실을 조사했다.
- 조사 결과는 이번 수정에 직접 대량 반영하지 않고, 리오/민민/루미의 기존 소재와 충돌하지 않는 참고 근거로만 보존했다.

### 왜

- 새 NPC나 새 퀘스트를 추가하지 않는 조건에서, 리오의 물리 증거와 말랑돼지/방울젤리/버섯 소재가 외부 원형과 어긋나지 않는지 확인하기 위해서다.

### 누가

- 작업자: Sisyphus.
- 외부 조사 보조: librarian background task.

### 언제

- 2026-06-29 Docker QA와 병행.

### 어디서

- 참고 출처: MapleStory Wiki의 Henesys, Green Mushroom, Pig, Pig Pasture, Ribbon Pig, Slime 관련 페이지와 보조 DB.
- 적용 위치: 이번에는 `rsc/data/npcs/mage_lumi.md`의 노출 제한 보정에만 간접 반영.

### 어떻게

- Pig/Ribbon Pig의 빠른 이동과 식별 단서, Slime류의 액체/반응 소재, Henesys의 mushroom/field 맥락을 기존 Hazel Village 소재와 비교했다.
- 프로젝트 정사로 외부 지명을 추가하지 않았고, 기존 NPC/퀘스트 범위 밖의 새 사실은 넣지 않았다.

## 2026-06-29 MapleStory 초반 퀘스트 상세 조사 보고서

### 무엇을

- Hazel Village 5개 퀘스트와 맞닿는 MapleStory 초반 퀘스트 자료를 공식/커뮤니티/DB 출처로 교차 조사했다.
- 조사 결과를 `.omo/ultraresearch/20260629-102430/SYNTHESIS.md`, `claim-ledger.md`, `expansion-log.md`에 정리했다.
- 이번 작업에서는 `rsc/data` 원천 데이터와 live Neo4j 데이터는 수정하지 않았다.

### 왜

- 사용자가 MapleStory 원형 퀘스트를 시작 조건부터 전체 흐름까지 알아야 한다고 요청했다.
- Hazel Village 데이터에 외부 원형을 반영하기 전에, 버전별 수량/보상/절차 차이를 분리해 기록해야 잘못된 단일 정답을 canonical data에 넣지 않을 수 있다.

### 누가

- 작업자: Sisyphus.
- 보조 조사: librarian background lanes를 시작했지만, 최종 보고서는 부모 세션에서 직접 확인한 접근 가능 출처를 기준으로 작성했다.

### 언제

- 2026-06-29 MapleStory 참고 퀘스트 상세 조사 단계.

### 어디서

- 조사 보고서: `.omo/ultraresearch/20260629-102430/`.
- 관련 Hazel 원천 확인 대상: `rsc/data/quests/q_glowing_mushroom.yaml`, `q_pig_escape.yaml`, `q_jelly_color.yaml`, `q_changed_signpost.yaml`, `q_main_spore_night.yaml`.
- 기록 위치: `docs/npc_persona_version_2/db_data_augmentation_log.md`.

### 어떻게

- MapleStory Wiki, Hidden Street 검색 색인, NiaMeowDB, YunaDB, Artale DB, 한국 커뮤니티/위키 자료를 비교했다.
- Hidden Street 본문 직접 fetch는 403으로 차단되어 검색 색인 excerpt를 낮은 신뢰도 근거로 분리 표기했다.
- 핵심 결론은 `Mrs. Ming Ming's First Worry`와 `Second Worry`의 수량/보상이 버전별로 크게 갈린다는 점이며, Hazel 데이터에는 원본 수량을 직접 복사하지 않는 것을 권장했다.

## 2026-06-29 MapleStory 배경 조사 결과 추가 반영

### 무엇을

- 뒤늦게 완료된 librarian background lanes 10개 결과를 수집해 기존 조사 보고서에 addendum으로 반영했다.
- `.omo/ultraresearch/20260629-102430/SYNTHESIS.md`, `claim-ledger.md`, `expansion-log.md`를 갱신했다.
- 여전히 `rsc/data` 원천 데이터와 live Neo4j 데이터는 수정하지 않았다.

### 왜

- 초기 보고서 작성 시 optional lane 결과가 아직 도착하지 않았고, 이후 완료 알림이 도착했다.
- 새 결과 중 Nexon Archive의 KMS식 밍밍부인 수량, Hidden Street current GMS의 `[Wanted] Green Mushrooms` 변형, WCR2/KMSDB의 한국어 명칭·스크립트 조각처럼 보고서 정확도를 높이는 내용이 있었다.

### 누가

- 작업자: Sisyphus.
- 보조 조사: Green Mushroom, Pig Ribbon, Chief Stan mushroom, Ming Ming, Korean community, Slime material, official archive background lanes.

### 언제

- 2026-06-29 background task 완료 알림 수신 후.

### 어디서

- 조사 보고서: `.omo/ultraresearch/20260629-102430/SYNTHESIS.md`.
- 검증표: `.omo/ultraresearch/20260629-102430/claim-ledger.md`.
- 진행 기록: `.omo/ultraresearch/20260629-102430/expansion-log.md`.
- 작업 기록: `docs/npc_persona_version_2/db_data_augmentation_log.md`.

### 어떻게

- 완료된 background output을 모두 수집하고 기존 보고서와 충돌·보강되는 지점을 분류했다.
- 핵심 결론은 바꾸지 않았다. MapleStory 원본 수량은 lineage별 참고값으로 유지하고, Hazel canonical data에는 직접 복사하지 않는다는 결론을 강화했다.

## 2026-06-29 canonical story data 실제 증강

### 무엇을

- `rsc/data` 백업을 만든 뒤 기존 NPC 4명과 기존 퀘스트 5개 안에서만 데이터를 증강했다.
- 새 NPC나 새 퀘스트를 만들지 않고, 기존 NPC별 `KnowledgeChunk`를 1개씩 추가해 총 26개에서 30개로 늘렸다.
- 추가 chunk는 `minmin_chronicle_009`, `rio_chronicle_007`, `lumi_chronicle_006`, `rowan_chronicle_008`이다.
- 각 퀘스트 YAML의 `story_expansion`에 한국어 6하원칙 `six_w_log`를 추가했다.

### 왜

- 사용자가 보고서 작성이 아니라 기존 Hazel Village 원천 데이터 자체의 증강을 요청했다.
- 리오의 물리 증거, 민민 부인의 생활 기록, 루미의 표본 관찰, 로완의 중간 대조 질문을 보강해 Retrieval이 더 많은 근거를 제공하도록 하기 위해서다.
- MapleStory 조사 결과는 원본 수량과 보상을 복사하지 않고, 초반 생물 관찰·물리 단서·반응 비교 구조만 참고해야 했다.

### 누가

- 작업자: Sisyphus.
- 승인자: 사용자. “기존 데이터들을 백업한뒤에 다시 조사를 진행해서 데이터 증강”을 지시했다.

### 언제

- 2026-06-29, 백업 `output/backups/rsc-data-before-augmentation-20260629-211951.zip` 생성 후.

### 어디서

- NPC 원천: `rsc/data/npcs/minmin_lady.md`, `patrol_leader_rio.md`, `mage_lumi.md`, `chief_rowan.md`.
- 퀘스트 원천: `rsc/data/quests/q_glowing_mushroom.yaml`, `q_pig_escape.yaml`, `q_jelly_color.yaml`, `q_changed_signpost.yaml`, `q_main_spore_night.yaml`.
- live Neo4j에는 이 단계에서 반영하지 않았다. DB reset도 실행하지 않았다.

### 어떻게

- 먼저 회귀 테스트를 30개 chunk와 `six_w_log`를 기대하도록 바꾸고, 데이터 수정 전 실패를 확인했다.
- 이후 기존 ID만 참조하는 비정답 chunk 4개를 추가했다. 신규 chunk는 모두 `answer_sensitive: false`, `hint_level: 2` 이하로 유지했다.
- 각 퀘스트에 `누가`, `언제`, `어디서`, `무엇을`, `어떻게`, `왜` 값을 한국어 문장으로 추가했다.
- 검증에서 `uv run --frozen python -m unittest test_script.test_story_source_contract test_script.test_quest_ui_defaults test_script.test_deployment_contract`가 32개 테스트 통과로 끝났다.
- `uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j --report-path output/reports/neo4j_story_source_import_report.md` 출력에서 NPC 4, Location 8, Quest 5, Role 4, Event 5, Clue 8, Truth 3, KnowledgeChunk 30을 확인했다.
- `uv run --frozen python scripts/story_pipeline/validate_data.py`는 `Validation PASS`로 끝났다.
- `docker ps --filter "name=hazel_design_test"` 결과 실행 중인 설계 검증 컨테이너가 없었다.

## 2026-06-30 개발 Docker DB 반영 및 시나리오 QA 기록

### 무엇을

- `compose.design-test.yaml` 기반 개발 Docker 스택에 증강된 `rsc/data`를 `--reset` 없이 병합 적재했다.
- 개발 Neo4j에서 `KnowledgeChunk` 총 30개와 NPC별 분포 `chief_rowan: 8`, `mage_lumi: 6`, `minmin_lady: 9`, `patrol_leader_rio: 7`을 확인했다.
- 신규 chunk `minmin_chronicle_009`, `rio_chronicle_007`, `lumi_chronicle_006`, `rowan_chronicle_008`이 모두 live 개발 DB에 존재하고 `answer_sensitive: false`, `hint_level: 2`로 유지되는지 확인했다.

### 왜

- canonical source 증강이 실제 개발 Neo4j 검색 그래프에 반영됐는지 확인해야 했다.
- 운영 서버 설정이나 운영 DB를 건드리지 않고, 개발 서버 설정만으로 유저 추리 기반 퀘스트 진행 QA를 수행해야 했다.

### 누가

- 작업자: Sisyphus.
- 승인자: 사용자. 개발 서버 설정으로 진행하고 운영 설정은 유지하라고 지시했다.

### 언제

- 2026-06-30 개발 Docker 시나리오 QA 단계.

### 어디서

- Docker project: `hazel_design_test`.
- 개발 Streamlit: `http://127.0.0.1:18501`.
- 개발 Neo4j Bolt: `127.0.0.1:17687`.
- 개발 vLLM: `http://127.0.0.1:18000`, 모델 `google/gemma-4-E2B-it`.

### 어떻게

- `.env.design-test`가 없어 운영 `.env` 대신 `.env.design-test.example`을 명시 사용했다.
- `docker compose -f compose.design-test.yaml --env-file .env.design-test.example --profile gpu`만 사용해 개발 스택을 띄웠다.
- 기존 Streamlit 이미지가 26개 chunk를 포함한 상태임을 dry-run으로 발견해, 개발용 Streamlit 이미지만 rebuild/recreate한 뒤 다시 dry-run에서 `KnowledgeChunk: 30`을 확인했다.
- `docker exec hazel_design_test-streamlit-1 uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --database neo4j --report-path output/reports/design_test_live_import_report.md`로 reset 없이 병합 적재했다.
- `cypher-shell` 조회로 live 개발 DB 카운트와 신규 chunk 속성을 검증했다.

### 검증 결과

- live 개발 Neo4j의 `KnowledgeChunk` 총합은 30개였다.
- NPC별 분포는 `chief_rowan: 8`, `mage_lumi: 6`, `minmin_lady: 9`, `patrol_leader_rio: 7`이었다.
- 신규 chunk `minmin_chronicle_009`, `rio_chronicle_007`, `lumi_chronicle_006`, `rowan_chronicle_008`은 모두 `answer_sensitive: false`, `hint_level: 2`로 조회됐다.
- 개발 vLLM `/v1/models`는 `google/gemma-4-E2B-it`만 반환했다.

## 2026-06-30 품질 QA 기반 데이터 노출 확인

### 무엇을

- 개발 DB의 30개 `KnowledgeChunk`를 대상으로 NPC별 단서 노출과 로완 최종 공개 gate를 실제 E2B 응답 품질까지 포함해 확인했다.
- 별도 canonical data 수정이나 Neo4j reset은 실행하지 않았다.

### 왜

- 단순히 DB에 chunk가 존재하는 것만으로는 NPC가 자기 권한보다 앞선 전말을 말하지 않는지 보장할 수 없다.
- 사용자 요구는 “응답이 존재한다”가 아니라, 각 NPC가 단계별 힌트 품질을 만족하고 로완이 미완료 단서를 되돌리며 최종 단계에서만 전말을 공개하는지 확인하는 것이었다.

### 누가

- 작업자: Sisyphus.
- 승인자: 사용자.

### 언제

- 2026-06-30 개발 Docker 시나리오 QA 및 prompt/guidance 보정 후.

### 어디서

- 개발 Streamlit/vLLM/Neo4j stack: `hazel_design_test`.
- 품질 QA 보고서: `output/reports/quest_scenario_quality_20260630.md`, `output/reports/quest_scenario_quality_20260630.json`.

### 어떻게

- host에서 `PYTHONPATH=.`를 설정하고 `uv run --frozen python test_script/run_quest_scenario_quality.py`를 실행했다.
- QA는 11개 턴의 `quest_state`, route, missing clue, answer-sensitive retrieval, 모델 응답 핵심 단어 조합을 함께 검사했다.
- 로완 partial에서는 answer-sensitive chunk가 검색되지 않고 `clue_root_marks` 누락으로 리오/표지판 퀘스트에 되돌아가는지 확인했다.
- 로완 final에서는 `rowan_chronicle_005`, `rowan_chronicle_006`, `rowan_chronicle_007`, `rowan_chronicle_001` 같은 answer-sensitive chunk가 허용되고 `truth_moonwell_mana_cycle`이 공개되는지 확인했다.

### 검증 결과

- 품질 QA는 `PASS quality QA records=11`로 끝났다.
- 최종 상태는 `chief_rowan / q_main_spore_night / solved`였다.
- 최종 공개 truth는 `truth_moonwell_mana_cycle`이었다.
- 로완 partial route는 `patrol_leader_rio / q_changed_signpost`였고, 누락 단서는 `clue_root_marks`였다.
