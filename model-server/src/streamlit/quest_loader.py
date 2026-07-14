from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from src.streamlit.quest_types import (
    AnswerRevealPolicy,
    CHIEF_NPC_ID,
    ClueInfo,
    QuestRule,
    QuestRuleSet,
    QuestStep,
    TruthInfo,
    WrongHypothesis,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_DIR = ROOT / "rsc" / "data"


def load_quest_rule_set(source_dir: Path | None = None) -> QuestRuleSet:
    if source_dir is None:
        source_dir = Path(os.getenv("QUEST_SOURCE_DIR", str(DEFAULT_SOURCE_DIR)))
    clues = _load_clues(source_dir / "world" / "clues.yaml")
    truths = _load_truths(source_dir / "world" / "truths.yaml")
    quests = {
        quest.quest_id: quest
        for quest in (_load_quest(path) for path in sorted((source_dir / "quests").glob("*.yaml")))
    }
    return QuestRuleSet(quests=quests, clues=clues, truths=truths)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise TypeError(f"YAML mapping expected: {path}")
    return data


def _load_clues(path: Path) -> dict[str, ClueInfo]:
    data = _load_yaml(path)
    return {
        str(item["clue_id"]): ClueInfo(
            clue_id=str(item["clue_id"]),
            name=str(item.get("name", item["clue_id"])),
            hint_level=int(item.get("hint_level", 0)),
            truth_ids=tuple(str(truth_id) for truth_id in item.get("truth_ids", [])),
        )
        for item in data.get("clues", [])
        if isinstance(item, dict)
    }


def _load_truths(path: Path) -> dict[str, TruthInfo]:
    data = _load_yaml(path)
    truths: dict[str, TruthInfo] = {}
    for item in data.get("truths", []):
        if not isinstance(item, dict):
            continue
        conditions = item.get("reveal_conditions", {})
        required = conditions.get("required_clue_ids", []) if isinstance(conditions, dict) else []
        truth_id = str(item["truth_id"])
        truths[truth_id] = TruthInfo(
            truth_id=truth_id,
            name=str(item.get("name", truth_id)),
            required_clue_ids=tuple(str(clue_id) for clue_id in required),
        )
    return truths


def _load_quest(path: Path) -> QuestRule:
    data = _load_yaml(path)
    expansion = data.get("story_expansion", {})
    steps = expansion.get("quest_steps", []) if isinstance(expansion, dict) else []
    wrong_hypotheses = expansion.get("wrong_hypotheses", []) if isinstance(expansion, dict) else []
    reveal_policy = expansion.get("answer_reveal_policy", {}) if isinstance(expansion, dict) else {}
    return QuestRule(
        quest_id=str(data["quest_id"]),
        title=str(data.get("title", data["quest_id"])),
        involved_npc_ids=tuple(str(npc_id) for npc_id in data.get("involved_npc_ids", [])),
        required_clue_ids=tuple(str(clue_id) for clue_id in data.get("required_clue_ids", [])),
        answer_truth_ids=tuple(str(truth_id) for truth_id in data.get("answer_truth_ids", [])),
        steps=tuple(_parse_step(item) for item in steps if isinstance(item, dict)),
        wrong_hypotheses=tuple(_parse_wrong_hypothesis(item) for item in wrong_hypotheses if isinstance(item, dict)),
        answer_reveal_policy=_parse_answer_reveal_policy(reveal_policy, data.get("required_clue_ids", [])),
    )


def _parse_step(item: dict[str, Any]) -> QuestStep:
    return QuestStep(
        step_id=str(item["step_id"]),
        title=str(item.get("title", "")),
        objective=str(item.get("objective", "")),
        npc_id=str(item.get("npc_id", "")),
        player_observation=str(item.get("player_observation", "")),
        npc_hint=str(item.get("npc_hint", "")),
        unlocked_clue_ids=tuple(str(clue_id) for clue_id in item.get("unlocked_clue_ids", [])),
        next_step_condition=str(item.get("next_step_condition", "")),
    )


def _parse_wrong_hypothesis(item: dict[str, Any]) -> WrongHypothesis:
    return WrongHypothesis(
        hypothesis_id=str(item["hypothesis_id"]),
        text=str(item.get("text", "")),
        disproof_clue_ids=tuple(str(clue_id) for clue_id in item.get("disproof_clue_ids", [])),
        npc_reaction=str(item.get("npc_reaction", "")),
    )


def _parse_answer_reveal_policy(policy: Any, required_clue_ids: Any) -> AnswerRevealPolicy:
    if not isinstance(policy, dict):
        policy = {}
    return AnswerRevealPolicy(
        can_reveal_truth_before_required_clues=bool(policy.get("can_reveal_truth_before_required_clues", False)),
        required_before_reveal=_string_tuple(policy.get("required_before_reveal", required_clue_ids)),
        npc_allowed_to_reveal=_string_tuple(policy.get("npc_allowed_to_reveal", (CHIEF_NPC_ID,))),
        npc_not_allowed_to_reveal=_string_tuple(policy.get("npc_not_allowed_to_reveal", ())),
    )


def _string_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, list | tuple):
        return tuple(str(item) for item in value)
    if isinstance(value, str):
        return (value,)
    return ()
