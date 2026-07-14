from __future__ import annotations

from functools import lru_cache
from typing import Any

from src.streamlit.quest_graph import build_quest_graph
from src.streamlit.quest_loader import load_quest_rule_set
from src.streamlit.quest_types import QUEST_STATE_HINT_LEVELS, QuestDecision, QuestGraphState


@lru_cache(maxsize=1)
def get_quest_graph():
    return build_quest_graph(load_quest_rule_set())


def make_thread_id(session_id: str, npc_id: str, quest_id: str) -> str:
    return f"session:{session_id}:npc:{npc_id}:quest:{quest_id}"


def run_quest_turn(
    session_id: str,
    npc_id: str,
    quest_id: str,
    user_message: str,
    quest_state_by_quest: dict[str, str],
    observed_clue_ids_by_quest: dict[str, list[str]],
) -> QuestDecision:
    graph = get_quest_graph()
    config = {"configurable": {"thread_id": make_thread_id(session_id, npc_id, quest_id)}}
    merged_observed = _merge_checkpoint_observed(graph.get_state(config).values, observed_clue_ids_by_quest)
    state: QuestGraphState = {
        "npc_id": npc_id,
        "quest_id": quest_id,
        "user_message": user_message,
        "quest_state_by_quest": quest_state_by_quest,
        "observed_clue_ids_by_quest": merged_observed,
    }
    result = graph.invoke(state, config)
    return _decision_from_record(result["decision"])


def _merge_checkpoint_observed(
    checkpoint_values: dict[str, Any],
    observed_clue_ids_by_quest: dict[str, list[str]],
) -> dict[str, list[str]]:
    merged = {quest_id: list(clue_ids) for quest_id, clue_ids in observed_clue_ids_by_quest.items()}
    checkpoint_observed = checkpoint_values.get("observed_clue_ids_by_quest")
    if not isinstance(checkpoint_observed, dict):
        return merged
    for quest_id, clue_ids in checkpoint_observed.items():
        if not isinstance(quest_id, str) or not isinstance(clue_ids, list):
            continue
        existing = merged.setdefault(quest_id, [])
        for clue_id in clue_ids:
            if isinstance(clue_id, str) and clue_id not in existing:
                existing.append(clue_id)
    return merged


def apply_decision_to_maps(
    decision: QuestDecision,
    quest_state_by_quest: dict[str, str],
    allowed_hint_level_by_quest: dict[str, int],
    observed_clue_ids_by_quest: dict[str, list[str]],
) -> None:
    quest_state_by_quest[decision.quest_id] = decision.quest_state
    allowed_hint_level_by_quest[decision.quest_id] = decision.allowed_hint_level
    observed_clue_ids_by_quest[decision.quest_id] = list(decision.observed_clue_ids)


def hint_level_for_state(quest_state: str) -> int:
    return QUEST_STATE_HINT_LEVELS.get(quest_state, 1)


def _decision_from_record(record: dict[str, Any]) -> QuestDecision:
    return QuestDecision(
        npc_id=str(record["npc_id"]),
        quest_id=str(record["quest_id"]),
        quest_state=str(record["quest_state"]),
        allowed_hint_level=int(record["allowed_hint_level"]),
        observed_clue_ids=tuple(str(value) for value in record["observed_clue_ids"]),
        newly_unlocked_clue_ids=tuple(str(value) for value in record["newly_unlocked_clue_ids"]),
        route_to_npc_id=str(record["route_to_npc_id"]) if record.get("route_to_npc_id") else None,
        route_to_quest_id=str(record["route_to_quest_id"]) if record.get("route_to_quest_id") else None,
        missing_clue_ids=tuple(str(value) for value in record["missing_clue_ids"]),
        disproof_clue_ids=tuple(str(value) for value in record["disproof_clue_ids"]),
        reveal_truth_ids=tuple(str(value) for value in record["reveal_truth_ids"]),
        guidance=str(record["guidance"]),
        reason=str(record["reason"]),
    )
