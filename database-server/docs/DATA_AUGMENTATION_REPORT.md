# 데이터 증강 결과 보고서

> 이 문서는 2026-06 데이터 증강 결과 기록이다. 현재 storage와 runtime 경계는 [README.md](README.md)와 [db_design.md](db_design.md)를 우선한다.

## 1. 작업 요약

이번 증강은 기존 프로젝트 구조를 유지하면서 NPC별 지식 밀도를 늘린 작업이다. 새 NPC와 새 퀘스트는 추가하지 않았다.

| 항목 | 결과 |
|---|---:|
| NPC 수 | 4 |
| Quest 수 | 5 |
| Clue 수 | 8 |
| Truth 수 | 3 |
| KnowledgeChunk 수 | 30 |

증강 전에는 `KnowledgeChunk`가 26개였고, 이번 작업에서 기존 NPC 4명에게 각 1개씩 총 4개를 추가했다.

## 2. 수정된 원천 데이터 파일

| 파일 | 추가 내용 |
|---|---|
| `rsc/data/npcs/minmin_lady.md` | `minmin_chronicle_009` 추가 |
| `rsc/data/npcs/patrol_leader_rio.md` | `rio_chronicle_007` 추가 |
| `rsc/data/npcs/mage_lumi.md` | `lumi_chronicle_006` 추가 |
| `rsc/data/npcs/chief_rowan.md` | `rowan_chronicle_008` 추가 |
| `rsc/data/quests/q_glowing_mushroom.yaml` | `story_expansion.six_w_log` 추가 |
| `rsc/data/quests/q_pig_escape.yaml` | `story_expansion.six_w_log` 추가 |
| `rsc/data/quests/q_jelly_color.yaml` | `story_expansion.six_w_log` 추가 |
| `rsc/data/quests/q_changed_signpost.yaml` | `story_expansion.six_w_log` 추가 |
| `rsc/data/quests/q_main_spore_night.yaml` | `story_expansion.six_w_log` 추가 |

## 3. 추가된 KnowledgeChunk 목록

| chunk_id | NPC | quest_id | clue_ids | allowed_roles | hint_level | answer_sensitive |
|---|---|---|---|---|---:|---|
| `minmin_chronicle_009` | `minmin_lady` | `q_main_spore_night` | `clue_bright_mushroom`, `clue_pig_tracks`, `clue_moonlit_night` | `farmer`, `lord` | 2 | false |
| `rio_chronicle_007` | `patrol_leader_rio` | `q_changed_signpost` | `clue_changed_signpost`, `clue_root_marks` | `knight`, `lord` | 2 | false |
| `lumi_chronicle_006` | `mage_lumi` | `q_jelly_color` | `clue_jelly_color_change`, `clue_mana_reaction`, `clue_glittering_powder` | `mage`, `lord` | 2 | false |
| `rowan_chronicle_008` | `chief_rowan` | `q_main_spore_night` | `clue_bright_mushroom`, `clue_pig_tracks`, `clue_jelly_color_change`, `clue_changed_signpost` | `lord` | 2 | false |

## 4. 추가 chunk 원문 확인 지점

### `minmin_chronicle_009`

위치: `rsc/data/npcs/minmin_lady.md`

추가된 핵심 내용은 민민 부인이 이상한 밤마다 달력 가장자리에 남긴 밤별 장부다. 민민 부인은 날짜와 방향이 겹친다는 생활 기록만 말하고, 원인은 확정하지 않는다.

### `rio_chronicle_007`

위치: `rsc/data/npcs/patrol_leader_rio.md`

추가된 핵심 내용은 표지판 주변 뿌리 자국의 간격과 파편 방향 기록이다. 리오는 사람 발자국이 없다는 물리적 사실만 제시하고, 소문이나 범인 확정은 하지 않는다.

### `lumi_chronicle_006`

위치: `rsc/data/npcs/mage_lumi.md`

추가된 핵심 내용은 방울젤리 점액과 반짝이는 가루 표본의 약한 반응 기록이다. 루미는 표본이 같은 방향의 흐름을 가리킬 수 있다는 가설까지만 말한다.

### `rowan_chronicle_008`

위치: `rsc/data/npcs/chief_rowan.md`

추가된 핵심 내용은 최종 답 전 플레이어에게 네 사건의 시간대와 방향을 비교하게 하는 중간 대조 질문이다. `answer_sensitive: false`, `hint_level: 2`, `allowed_roles: lord`로 제한했다.

## 5. 퀘스트별 추가된 `story_expansion.six_w_log`

| quest_id | 추가된 6하원칙 기준 |
|---|---|
| `q_glowing_mushroom` | 민민의 최초 관찰, 달빛 조건, 숲 입구 현상, 루미 가설과 로완 보고 순서를 분리 |
| `q_pig_escape` | 말랑돼지 탈출을 먹이 문제가 아니라 방향, 발자국, 가루 단서로 추적 |
| `q_jelly_color` | 색 변화와 약한 반응 표본을 위치 비교와 가설 검증으로 연결 |
| `q_changed_signpost` | 장난 소문보다 사람 발자국 부재, 뿌리 자국, 파편 방향을 우선 검토 |
| `q_main_spore_night` | 앞선 네 사건의 빛, 발자국, 색 변화, 표지판 흔적을 최종 추론 직전 정리 |

## 6. NPC별 새로 말할 수 있는 정보

| NPC | 새로 말할 수 있는 정보 | 여전히 말하면 안 되는 정보 |
|---|---|---|
| 민민 부인 | 밤별 장부에 남은 날짜, 달빛, 말랑돼지 방향의 생활 기록 | 포자 냄새가 최종 원인이라는 확정 설명, 마나 원리 |
| 순찰대장 리오 | 표지판 주변 뿌리 자국 간격과 파편 방향이라는 물리 기록 | 마법 반응 원리, 최종 truth, 촌장 종합 판단 대리 공개 |
| 마도사 루미 | 방울젤리 표본과 반짝이는 가루의 약한 반응 가능성 | 최종 원인 단정, 표지판 범인 확정, 로완 기밀 판단 |
| 헤이즐 촌장 로완 | 최종 답 전 네 사건의 시간대와 방향을 묻는 중간 대조 질문 | 단서 부족 상태에서 결론 공개 |

## 7. 구조 유지 확인

- 새 NPC를 추가하지 않았다.
- 새 퀘스트를 추가하지 않았다.
- 새 `clue_id`와 `truth_id`를 추가하지 않았다.
- 새 대형 지역, 오브젝트, 생물 디렉터리를 만들지 않았다.
- GraphRAG 평가셋, JSONL, vector DB 확장은 추가하지 않았다.
- NPC 파일에는 각 NPC의 개인 지식과 관찰만 추가했고, 퀘스트 진행 전체는 `rsc/data/quests/*.yaml`에 유지했다.

## 8. 관련 설계 문서

이번 증강 기준은 `docs/plans/data-augmentation-design.md`에 정리했다. 이 문서는 증강 범위, NPC별 권한 설계, MapleStory 참고 원칙, 최종 보고서 요구사항을 포함한다.

## 9. 검증 결과

검증 결과는 모두 통과했다.

```text
uv run --frozen python -m unittest test_script.test_story_source_contract test_script.test_quest_ui_defaults test_script.test_deployment_contract test_script.test_study_docs_contract
-> Ran 43 tests
-> OK

uv run --frozen python -m compileall src test_script
-> PASS

uv run --frozen python scripts/story_pipeline/validate_data.py
-> Validation PASS

uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j --report-path output/reports/neo4j_story_source_import_report.md
-> Validation PASS
-> KnowledgeChunk: 30
```

Importer 기준 chunk 수 확인 결과는 다음과 같다.

```text
NPC: 4
KnowledgeChunk: 30
chief_rowan: 8
mage_lumi: 6
minmin_lady: 9
patrol_leader_rio: 7
```

이번 검증에서는 source importer dry-run으로 DB 접속 없이 원천 파싱 수와 관계 무결성을 확인했다.

## 10. Neo4j 원천 데이터 적재 설계

증강된 `KnowledgeChunk` 30개를 Streamlit GraphRAG에서 바로 사용하려면 `output/neo4j_import` CSV 로더가 아니라 원천 importer를 사용한다.

| 경로 | 용도 |
|---|---|
| `src/db_control/import_story_source_to_neo4j.py` | `rsc/data` 원천 Markdown/YAML을 읽어 `NPC`, `Quest`, `Clue`, `Truth`, `Location`, `Event`, `KnowledgeChunk` 그래프로 적재 |
| `scripts/story_pipeline/load_neo4j.py` | `output/neo4j_import/*.csv` 산출물을 적재하는 별도 경로. 현재 Streamlit이 조회하는 `KnowledgeChunk` 원천 그래프와는 목적이 다름 |

Streamlit 런타임은 다음 구조를 조회한다.

```cypher
MATCH (:NPC {npc_id: $npc_id})-[:KNOWS]->(k:KnowledgeChunk)
```

따라서 이번 증강 데이터의 운영 적재 기준은 `src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data`이다.

## 11. 개선된 importer 동작

`src/db_control/import_story_source_to_neo4j.py`는 증강 데이터가 늘어나도 안전하게 나누어 적재되도록 다음 기준으로 개선했다.

| 개선 항목 | 설계 |
|---|---|
| 사전 plan 생성 | `build_import_plan(source_dir)`가 DB 접속 전에 NPC, chunk, location, quest, world 데이터를 먼저 파싱한다. |
| 사전 검증 | `validate_import_plan(plan)`이 NPC 4명, Quest 5개, KnowledgeChunk 30개, NPC별 chunk 분포, 참조 ID 무결성을 검증한다. |
| dry-run | `--dry-run`은 Neo4j 패키지나 DB 접속 없이 원천 데이터 검증과 리포트 생성을 수행한다. |
| database 선택 | `--database` 또는 `NEO4J_DATABASE` 값을 `driver.execute_query(..., database_=...)`에 전달한다. |
| no-reset 기본값 | 기본 적재는 `MERGE` 기반 병합이며 `--reset`을 붙이지 않는다. |
| 관계 분할 적재 | Event, Clue, KnowledgeChunk 관계는 list가 비어 있어도 다른 관계 적재가 끊기지 않도록 독립 `FOREACH` 방식으로 처리한다. |
| stale 관계 정리 | 각 source 객체가 소유한 outgoing 관계만 삭제 후 재생성한다. 노드 전체 삭제나 DB 전체 reset은 하지 않는다. |
| source import report | `output/reports/neo4j_story_source_import_report.md`에 source count, relationship count, loaded count, validation 결과를 기록한다. |

## 12. Neo4j 적재 명령

이번 증강 작업에서는 live Neo4j 재적재를 실행하지 않았다. design-test Neo4j에 반영해야 할 때는 Docker가 올라간 상태에서 bolt port `127.0.0.1:17687`을 사용한다.

먼저 dry-run으로 원천 데이터와 관계 수를 확인한다.

```powershell
$env:NEO4J_DATABASE="neo4j"
uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --dry-run --database neo4j
```

Docker Neo4j에 병합 적재할 때는 `--reset` 없이 실행한다.

```powershell
$env:NEO4J_URI="bolt://localhost:17687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="<neo4j-password>"
$env:NEO4J_DATABASE="neo4j"
uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --database neo4j
```

정상 적재 후에는 다음 쿼리로 확인한다.

```cypher
MATCH (n:NPC)-[:KNOWS]->(k:KnowledgeChunk)
RETURN n.npc_id AS npc, count(k) AS chunks
ORDER BY npc;
```

기대값은 다음과 같다.

```text
chief_rowan: 8
mage_lumi: 6
minmin_lady: 9
patrol_leader_rio: 7
```

## 13. 이전 Neo4j 적재 결과

아래 결과는 2026-06-29 Docker QA 당시 `KnowledgeChunk` 26개 원천을 `--reset` 없이 병합 적재한 기록이다. 현재 canonical source는 `KnowledgeChunk` 30개로 증강됐으며, 이번 증강 작업에서는 live Neo4j 재적재를 실행하지 않았다.

실제 Docker Neo4j에 `--reset` 없이 병합 적재했다.

```powershell
$env:NEO4J_URI="bolt://localhost:17687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="<neo4j-password>"
$env:NEO4J_DATABASE="neo4j"
uv run --frozen python src/db_control/import_story_source_to_neo4j.py --source-dir rsc/data --database neo4j
```

실행 결과는 다음과 같다.

```text
Import complete.
- NPCs: 4
- Locations: 8
- Quests: 5
- Roles: 4
- Events: 5
- Clues: 8
- Truths: 3
- KnowledgeChunks: 26
```

Docker 컨테이너 내부에서 확인한 label별 노드 수는 다음과 같다.

```text
["Clue"]: 8
["Event"]: 5
["KnowledgeChunk"]: 26
["Location"]: 8
["NPC"]: 4
["Quest"]: 5
["Role"]: 4
["Truth"]: 3
```

NPC별 `KNOWS` 관계 기준 chunk 수는 다음과 같다.

```text
chief_rowan: 7
mage_lumi: 5
minmin_lady: 8
patrol_leader_rio: 6
```

같은 결과는 `output/reports/neo4j_story_source_import_report.md`에도 기록된다. 해당 보고서는 `mode: import`, `reset: false`, `database: neo4j`, `validation: PASS`와 source/relationship/loaded count를 포함한다.
