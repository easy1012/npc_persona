from __future__ import annotations

from dataclasses import dataclass
import json
import sys
from typing import Final
from uuid import uuid4

from src.streamlit.quest_runtime import apply_decision_to_maps, run_quest_turn
from src.streamlit.quest_types import DEFAULT_QUEST_STATE, FINAL_QUEST_ID, QUEST_OPTIONS


@dataclass(frozen=True, slots=True)
class QueryScenario:
    label: str
    npc_id: str
    quest_id: str
    player_role: str
    message: str
    expected_state: str
    expected_hint_level: int
    expected_new_clues: tuple[str, ...]
    quality_groups: tuple[tuple[str, ...], ...]


QUALITY_TURNS: Final[tuple[QueryScenario, ...]] = (
    QueryScenario(
        "minmin-neutral-greeting",
        "minmin_lady",
        "q_glowing_mushroom",
        "farmer",
        "안녕하세요. 건강하신가요?",
        "in_progress",
        1,
        (),
        (),
    ),
    QueryScenario(
        "minmin-1-bright-mushroom",
        "minmin_lady",
        "q_glowing_mushroom",
        "farmer",
        "밤에만 눈에 띄는 빛과 주변 가루를 본다. 낮과 밤을 나누어 보렴.",
        "hint_1_given",
        1,
        ("clue_bright_mushroom",),
        (("버섯", "빛"), ("밤", "빛")),
    ),
    QueryScenario(
        "minmin-2-moonlit-night",
        "minmin_lady",
        "q_glowing_mushroom",
        "farmer",
        "민민 부인의 기억이 달 밝은 밤에 집중된다. 달이 밝으면 더 보였단다.",
        "ready_to_answer",
        3,
        ("clue_moonlit_night",),
        (("달", "버섯"), ("달", "빛")),
    ),
    QueryScenario(
        "rio-neutral-patrol",
        "patrol_leader_rio",
        "q_pig_escape",
        "knight",
        "안녕하세요. 건강하신가요?",
        "in_progress",
        1,
        (),
        (),
    ),
    QueryScenario(
        "rio-1-pig-tracks",
        "patrol_leader_rio",
        "q_pig_escape",
        "knight",
        "말랑돼지 발자국이 숲 입구 쪽으로 이어진다. 방향을 봐라.",
        "hint_1_given",
        1,
        ("clue_pig_tracks",),
        (("발자국", "숲"), ("방향", "흔적")),
    ),
    QueryScenario(
        "rio-2-glittering-powder",
        "patrol_leader_rio",
        "q_pig_escape",
        "knight",
        "가루가 발자국 주변에서 발견된다. 정체는 몰라도 같은 현장에 있다.",
        "ready_to_answer",
        3,
        ("clue_glittering_powder",),
        (("가루", "발자국"), ("가루", "움직")),
    ),
    QueryScenario(
        "rio-jelly-color-observation",
        "patrol_leader_rio",
        "q_jelly_color",
        "knight",
        "평소보다 진한 색을 띠는 방울젤리 개체가 보인다. 가까이 가되 방심하지 마라.",
        "hint_2_given",
        2,
        ("clue_jelly_color_change",),
        (("방울젤리", "색"), ("변화", "기록")),
    ),
    QueryScenario(
        "lumi-neutral-theory",
        "mage_lumi",
        "q_jelly_color",
        "mage",
        "안녕하세요. 차를 한 잔 마셔도 될까요?",
        "hint_2_given",
        2,
        (),
        (),
    ),
    QueryScenario(
        "lumi-mana-reaction",
        "mage_lumi",
        "q_jelly_color",
        "mage",
        "루미의 도구가 약한 반응을 보인다. 결정적 답은 아니지만 흐름은 있어.",
        "ready_to_answer",
        3,
        ("clue_mana_reaction",),
        (("마나", "반응"), ("흐름", "반응"), ("단서", "반응")),
    ),
    QueryScenario(
        "rio-signpost-changed",
        "patrol_leader_rio",
        "q_changed_signpost",
        "knight",
        "표지판 방향이 평소와 다르다. 표지판만 보지 말고 주변을 봐라.",
        "hint_1_given",
        1,
        ("clue_changed_signpost",),
        (("표지판", "방향"), ("주변", "흔적"), ("경로", "확인")),
    ),
    QueryScenario(
        "minmin-signpost-rumor",
        "minmin_lady",
        "q_changed_signpost",
        "farmer",
        "장난기 많은 숲속 생물 이야기를 듣지만 확정하지 않는다.",
        "hint_1_given",
        1,
        (),
        (("소문", "직접"), ("숲", "살펴")),
    ),
    QueryScenario(
        "rio-root-marks",
        "patrol_leader_rio",
        "q_changed_signpost",
        "knight",
        "사람 발자국 대신 뿌리 자국과 나뭇조각이 보인다. 사람이 한 흔적은 아니다.",
        "ready_to_answer",
        3,
        ("clue_root_marks",),
        (("뿌리", "나뭇조각"), ("사람", "흔적")),
    ),
)

ROWAN_PARTIAL: Final = QueryScenario(
    "rowan-partial-routes-back-to-rio",
    "chief_rowan",
    FINAL_QUEST_ID,
    "lord",
    "버섯 빛, 돼지 발자국, 젤리 색, 표지판 변화, 반짝이는 가루를 합치면 밤의 마나와 포자가 원인인 것 같아요. 이게 최종 답인가요?",
    "ready_to_answer",
    3,
    (),
    (("순찰대장 리오", "표지판", "뿌리"), ("리오", "남은 단서", "확인")),
)

ROWAN_FINAL: Final = QueryScenario(
    "rowan-final-solves-with-all-ready",
    "chief_rowan",
    FINAL_QUEST_ID,
    "lord",
    "민민의 달 밝은 밤과 강한 버섯 빛, 리오의 숲 방향 발자국과 가루, 루미의 방울젤리 마나 반응, 표지판 주변의 뿌리 자국까지 모두 합치면 달빛 샘터의 마나 주기 강화가 포자와 생물 반응을 일으킨 것이 정답 아닌가요?",
    "solved",
    3,
    (),
    (("달빛 샘터", "마나", "포자", "리오", "표지판"),),
)


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(detail)


def verify_query_matrix() -> None:
    states = {quest_id: DEFAULT_QUEST_STATE for quest_id in QUEST_OPTIONS}
    levels = {quest_id: 1 for quest_id in QUEST_OPTIONS}
    observed: dict[str, list[str]] = {quest_id: [] for quest_id in QUEST_OPTIONS}
    session_id = uuid4().hex
    results: list[dict[str, str | int]] = []

    for scenario in QUALITY_TURNS:
        decision = run_quest_turn(
            session_id=session_id,
            npc_id=scenario.npc_id,
            quest_id=scenario.quest_id,
            user_message=scenario.message,
            quest_state_by_quest=states,
            observed_clue_ids_by_quest=observed,
        )
        _require(decision.quest_state == scenario.expected_state, f"{scenario.label}: state {decision.quest_state}")
        _require(decision.allowed_hint_level == scenario.expected_hint_level, f"{scenario.label}: hint {decision.allowed_hint_level}")
        _require(decision.newly_unlocked_clue_ids == scenario.expected_new_clues, f"{scenario.label}: clues {decision.newly_unlocked_clue_ids}")
        apply_decision_to_maps(decision, states, levels, observed)
        results.append({"npc_id": scenario.npc_id, "state": decision.quest_state, "hint": decision.allowed_hint_level})

    partial_states = dict(states)
    partial_observed = {quest_id: list(clue_ids) for quest_id, clue_ids in observed.items()}
    partial_states["q_changed_signpost"] = "hint_1_given"
    partial_observed["q_changed_signpost"] = ["clue_changed_signpost"]
    partial = run_quest_turn(
        session_id=uuid4().hex,
        npc_id=ROWAN_PARTIAL.npc_id,
        quest_id=ROWAN_PARTIAL.quest_id,
        user_message=ROWAN_PARTIAL.message,
        quest_state_by_quest=partial_states,
        observed_clue_ids_by_quest=partial_observed,
    )
    _require(partial.quest_state == ROWAN_PARTIAL.expected_state, "rowan partial state")
    _require(partial.route_to_npc_id == "patrol_leader_rio", "rowan partial route")
    _require("clue_root_marks" in partial.missing_clue_ids, "rowan partial missing clue")
    results.append({"npc_id": ROWAN_PARTIAL.npc_id, "state": partial.quest_state, "hint": partial.allowed_hint_level})

    final = run_quest_turn(
        session_id=uuid4().hex,
        npc_id=ROWAN_FINAL.npc_id,
        quest_id=ROWAN_FINAL.quest_id,
        user_message=ROWAN_FINAL.message,
        quest_state_by_quest=states,
        observed_clue_ids_by_quest=observed,
    )
    _require(final.quest_state == ROWAN_FINAL.expected_state, "rowan final state")
    _require(final.reveal_truth_ids == ("truth_moonwell_mana_cycle",), "rowan final truth")
    results.append({"npc_id": ROWAN_FINAL.npc_id, "state": final.quest_state, "hint": final.allowed_hint_level})

    print(f"PASS npc query matrix scenarios={len(results)}")
    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    _require("--verify" in sys.argv, "run with --verify")
    verify_query_matrix()
