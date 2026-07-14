from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from typing_extensions import NotRequired, TypedDict


@dataclass(frozen=True, slots=True)
class NpcMetadata:
    player_role: str
    quest_id: str


DEFAULT_NPC_ID: Final = "minmin_lady"
DEFAULT_PLAYER_ROLE: Final = "farmer"
DEFAULT_QUEST_ID: Final = "q_glowing_mushroom"
DEFAULT_QUEST_STATE: Final = "in_progress"
DEFAULT_HINT_LEVEL: Final = 1

NPC_METADATA: Final[dict[str, NpcMetadata]] = {
    "minmin_lady": NpcMetadata(player_role="farmer", quest_id="q_glowing_mushroom"),
    "patrol_leader_rio": NpcMetadata(player_role="knight", quest_id="q_pig_escape"),
    "mage_lumi": NpcMetadata(player_role="mage", quest_id="q_jelly_color"),
    "chief_rowan": NpcMetadata(player_role="lord", quest_id="q_main_spore_night"),
}

NPC_NAMES: Final[dict[str, str]] = {
    "minmin_lady": "민민 부인",
    "patrol_leader_rio": "순찰대장 리오",
    "mage_lumi": "마도사 루미",
    "chief_rowan": "헤이즐 촌장 로완",
}

NPC_OPTIONS: Final[tuple[str, ...]] = tuple(NPC_METADATA)
ROLE_OPTIONS: Final[tuple[str, ...]] = ("farmer", "knight", "mage", "lord")

QUEST_OPTIONS: Final[tuple[str, ...]] = (
    "q_glowing_mushroom",
    "q_pig_escape",
    "q_jelly_color",
    "q_changed_signpost",
    "q_main_spore_night",
)

QUEST_DEFAULT_NPC_IDS: Final[dict[str, str]] = {
    "q_glowing_mushroom": "minmin_lady",
    "q_pig_escape": "patrol_leader_rio",
    "q_jelly_color": "patrol_leader_rio",
    "q_changed_signpost": "patrol_leader_rio",
    "q_main_spore_night": "chief_rowan",
}

QUEST_STATE_OPTIONS: Final[tuple[str, ...]] = (
    "not_started",
    "in_progress",
    "hint_1_given",
    "hint_2_given",
    "ready_to_answer",
    "solved",
)

QUEST_STATE_HINT_LEVELS: Final[dict[str, int]] = {
    "not_started": 0,
    "in_progress": 1,
    "hint_1_given": 1,
    "hint_2_given": 2,
    "ready_to_answer": 3,
    "solved": 3,
}

CHIEF_NPC_ID = "chief_rowan"
FINAL_QUEST_ID = "q_main_spore_night"
PRE_FINAL_QUEST_IDS = (
    "q_glowing_mushroom",
    "q_pig_escape",
    "q_jelly_color",
    "q_changed_signpost",
)


@dataclass(frozen=True, slots=True)
class ClueInfo:
    clue_id: str
    name: str
    hint_level: int
    truth_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TruthInfo:
    truth_id: str
    name: str
    required_clue_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QuestStep:
    step_id: str
    title: str
    objective: str
    npc_id: str
    player_observation: str
    npc_hint: str
    unlocked_clue_ids: tuple[str, ...]
    next_step_condition: str


@dataclass(frozen=True, slots=True)
class WrongHypothesis:
    hypothesis_id: str
    text: str
    disproof_clue_ids: tuple[str, ...]
    npc_reaction: str


@dataclass(frozen=True, slots=True)
class AnswerRevealPolicy:
    can_reveal_truth_before_required_clues: bool
    required_before_reveal: tuple[str, ...]
    npc_allowed_to_reveal: tuple[str, ...]
    npc_not_allowed_to_reveal: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QuestRule:
    quest_id: str
    title: str
    involved_npc_ids: tuple[str, ...]
    required_clue_ids: tuple[str, ...]
    answer_truth_ids: tuple[str, ...]
    steps: tuple[QuestStep, ...]
    wrong_hypotheses: tuple[WrongHypothesis, ...]
    answer_reveal_policy: AnswerRevealPolicy


@dataclass(frozen=True, slots=True)
class QuestRuleSet:
    quests: dict[str, QuestRule]
    clues: dict[str, ClueInfo]
    truths: dict[str, TruthInfo]


@dataclass(frozen=True, slots=True)
class QuestTurnContext:
    npc_id: str
    quest_id: str
    user_message: str
    quest_state_by_quest: dict[str, str]
    observed_clue_ids_by_quest: dict[str, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class QuestDecision:
    npc_id: str
    quest_id: str
    quest_state: str
    allowed_hint_level: int
    observed_clue_ids: tuple[str, ...]
    newly_unlocked_clue_ids: tuple[str, ...]
    route_to_npc_id: str | None
    route_to_quest_id: str | None
    missing_clue_ids: tuple[str, ...]
    disproof_clue_ids: tuple[str, ...]
    reveal_truth_ids: tuple[str, ...]
    guidance: str
    reason: str

    def as_record(self) -> QuestDecisionRecord:
        return {
            "npc_id": self.npc_id,
            "quest_id": self.quest_id,
            "quest_state": self.quest_state,
            "allowed_hint_level": self.allowed_hint_level,
            "observed_clue_ids": list(self.observed_clue_ids),
            "newly_unlocked_clue_ids": list(self.newly_unlocked_clue_ids),
            "route_to_npc_id": self.route_to_npc_id,
            "route_to_quest_id": self.route_to_quest_id,
            "missing_clue_ids": list(self.missing_clue_ids),
            "disproof_clue_ids": list(self.disproof_clue_ids),
            "reveal_truth_ids": list(self.reveal_truth_ids),
            "guidance": self.guidance,
            "reason": self.reason,
        }


class QuestDecisionRecord(TypedDict):
    npc_id: str
    quest_id: str
    quest_state: str
    allowed_hint_level: int
    observed_clue_ids: list[str]
    newly_unlocked_clue_ids: list[str]
    route_to_npc_id: str | None
    route_to_quest_id: str | None
    missing_clue_ids: list[str]
    disproof_clue_ids: list[str]
    reveal_truth_ids: list[str]
    guidance: str
    reason: str


class QuestGraphState(TypedDict):
    npc_id: str
    quest_id: str
    user_message: str
    quest_state_by_quest: dict[str, str]
    observed_clue_ids_by_quest: dict[str, list[str]]
    decision: NotRequired[QuestDecisionRecord]
