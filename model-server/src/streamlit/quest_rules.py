from __future__ import annotations

import re

from src.streamlit.quest_types import (
    CHIEF_NPC_ID,
    FINAL_QUEST_ID,
    NPC_NAMES,
    PRE_FINAL_QUEST_IDS,
    QUEST_STATE_HINT_LEVELS,
    QuestDecision,
    QuestRule,
    QuestRuleSet,
    QuestStep,
    QuestTurnContext,
    WrongHypothesis,
)


FINAL_INTENT_MARKERS = ("정답", "원인", "결론", "비밀", "전말", "추리", "왜", "연결")
FINAL_TRUTH_MARKERS = {
    "truth_moonwell_mana_cycle": (
        "달빛 포자 반응",
        "달빛에 포자가 반응",
        "같은 밤의 영향",
        "버섯 돼지 젤리 표지판",
        "빛나고 숲으로 가고 색 변화 표지판",
    ),
    "truth_spore_scent_attraction": (
        "포자 냄새가 말랑돼지",
        "돼지가 숲으로",
        "가루 냄새를 따라",
    ),
    "truth_stump_followed_spores": (
        "포자 반응을 따라 움직",
        "표지판을 바꿈",
        "뿌리 자국 표지판",
    ),
}
COMMON_MARKER_TOKENS = {
    "가능성",
    "가설",
    "관찰",
    "기록",
    "단서",
    "답은",
    "듯이",
    "때만",
    "말한다",
    "묻는다",
    "방향",
    "보고",
    "본다",
    "아직",
    "않고",
    "위해",
    "조건",
    "주변",
    "직접",
    "확보",
    "확인",
    "확인한다",
}


def evaluate_quest_turn(rule_set: QuestRuleSet, context: QuestTurnContext) -> QuestDecision:
    quest = rule_set.quests[context.quest_id]
    observed = _observed_clues_for_context(context)
    matched_clues = _matched_step_clues(rule_set, quest, context.npc_id, observed, context.user_message)
    observed.update(matched_clues)

    wrong = _matched_wrong_hypothesis(quest, context.user_message)
    required_before_reveal = _required_before_reveal(quest)
    missing = tuple(clue_id for clue_id in required_before_reveal if clue_id not in observed)
    current_state = context.quest_state_by_quest.get(context.quest_id, "in_progress")
    state = _quest_state_for_observed(rule_set, quest, tuple(sorted(observed)), current_state)
    route_to_npc_id: str | None = None
    route_to_quest_id: str | None = None
    reveal_truth_ids: tuple[str, ...] = ()
    reason = "evidence_evaluated"

    if wrong is not None:
        disproof_clue_id = wrong.disproof_clue_ids[0] if wrong.disproof_clue_ids else ""
        route_to_npc_id = _npc_for_clue(rule_set, quest, disproof_clue_id)
        route_to_quest_id = _quest_for_clue(rule_set, disproof_clue_id)
        reason = "wrong_hypothesis"
        guidance = f"그 추리는 아직 맞지 않습니다. {wrong.npc_reaction} 관련 단서는 {_clue_names(rule_set, wrong.disproof_clue_ids)}입니다."
        return _decision(context, state, rule_set, observed, matched_clues, route_to_npc_id, route_to_quest_id, missing, wrong.disproof_clue_ids, reveal_truth_ids, guidance, reason)

    prospective_states = {**context.quest_state_by_quest, context.quest_id: state}
    if not _can_npc_reveal(quest, context.npc_id) and (_all_pre_final_ready(prospective_states) or (not missing and _has_final_intent(context.user_message, rule_set, quest))):
        route_to_npc_id = CHIEF_NPC_ID
        route_to_quest_id = FINAL_QUEST_ID
        reason = "route_to_chief"
        guidance = "필수 단서가 충분히 모였습니다. 이 NPC는 최종 전말을 확정하지 말고, 헤이즐 촌장 로완에게 종합 추리를 제시하라고 안내하세요."
        return _decision(context, state, rule_set, observed, matched_clues, route_to_npc_id, route_to_quest_id, missing, (), reveal_truth_ids, guidance, reason)

    if _can_npc_reveal(quest, context.npc_id) and not missing and _has_final_intent(context.user_message, rule_set, quest):
        final_score = _final_answer_score(rule_set, quest, context.user_message, tuple(sorted(observed)))
        if _mentions_answer_truth(rule_set, quest, context.user_message) and final_score >= _required_final_score(quest):
            incomplete_pre_final_quest_id = _first_incomplete_pre_final_quest(context.quest_state_by_quest)
            if incomplete_pre_final_quest_id is not None:
                incomplete_quest = rule_set.quests[incomplete_pre_final_quest_id]
                incomplete_observed = context.observed_clue_ids_by_quest.get(incomplete_pre_final_quest_id, ())
                incomplete_missing = tuple(
                    clue_id
                    for clue_id in _required_before_reveal(incomplete_quest)
                    if clue_id not in incomplete_observed
                )
                route_clue_id = incomplete_missing[0] if incomplete_missing else incomplete_quest.required_clue_ids[0]
                route_to_npc_id = _npc_for_clue(rule_set, incomplete_quest, route_clue_id)
                route_to_quest_id = incomplete_pre_final_quest_id
                route_npc_name = NPC_NAMES.get(route_to_npc_id, route_to_npc_id)
                reason = "chief_final_pre_final_incomplete"
                missing_names = _clue_names(rule_set, incomplete_missing)
                guidance = f"아직 마지막 NPC 보고와 단서 확인이 부족합니다. 최종 정답을 인정하지 마세요. 답변에 반드시 포함할 내용: {route_npc_name}에게 {incomplete_quest.title}의 남은 단서인 {missing_names} 확인이 부족하다. 표지판 주변의 뿌리 자국과 나뭇조각을 다시 확인해야 한다."
                return _decision(context, state, rule_set, observed, matched_clues, route_to_npc_id, route_to_quest_id, incomplete_missing, (), reveal_truth_ids, guidance, reason)

            state = "solved"
            reveal_truth_ids = quest.answer_truth_ids
            reason = "chief_final_correct"
            guidance = f"플레이어의 추리가 충분히 맞습니다. {_truth_names(rule_set, reveal_truth_ids)} 전말과 단서 연결고리를 직접 공개하고 완료를 인정하세요. 민민 부인, 순찰대장 리오, 마도사 루미의 보고가 달빛 샘터의 마나 주기 강화로 이어진다고 말하세요."
            return _decision(context, state, rule_set, observed, matched_clues, None, None, (), (), reveal_truth_ids, guidance, reason)

    if _can_npc_reveal(quest, context.npc_id) and (missing or _has_final_intent(context.user_message, rule_set, quest)):
        route_clue_id = missing[0] if missing else quest.required_clue_ids[0]
        route_to_npc_id = _npc_for_clue(rule_set, quest, route_clue_id)
        route_to_quest_id = _quest_for_clue(rule_set, route_clue_id)
        route_npc_name = NPC_NAMES.get(route_to_npc_id, route_to_npc_id)
        reason = "chief_final_partial"
        guidance = f"아직 빠진 근거와 단서 확인이 부족합니다. 답변에 반드시 포함할 내용: {route_npc_name}에게 남은 단서인 {_clue_names(rule_set, missing) or '단서 연결 설명'} 확인이 부족하니 다시 확인해야 한다."
        return _decision(context, state, rule_set, observed, matched_clues, route_to_npc_id, route_to_quest_id, missing, (), reveal_truth_ids, guidance, reason)

    guidance = _next_hint_guidance(rule_set, quest, tuple(sorted(observed)), matched_clues)
    return _decision(context, state, rule_set, observed, matched_clues, None, None, missing, (), reveal_truth_ids, guidance, reason)


def _observed_clues_for_context(context: QuestTurnContext) -> set[str]:
    observed = set(context.observed_clue_ids_by_quest.get(context.quest_id, ()))
    if context.quest_id == FINAL_QUEST_ID:
        for quest_id in PRE_FINAL_QUEST_IDS:
            observed.update(context.observed_clue_ids_by_quest.get(quest_id, ()))
    return observed


def _matched_step_clues(
    rule_set: QuestRuleSet,
    quest: QuestRule,
    npc_id: str,
    observed: set[str],
    user_message: str,
) -> tuple[str, ...]:
    matches: list[str] = []
    for step in quest.steps:
        if step.npc_id != npc_id:
            continue
        new_clues = [clue_id for clue_id in step.unlocked_clue_ids if clue_id not in observed]
        if new_clues and _matches_step(rule_set, step, user_message):
            matches.extend(new_clues)
    return tuple(dict.fromkeys(matches))


def _matches_step(rule_set: QuestRuleSet, step: QuestStep, user_message: str) -> bool:
    for clue_id in step.unlocked_clue_ids:
        clue = rule_set.clues.get(clue_id)
        clue_markers = (clue_id,) if clue is None else (clue_id, clue.name)
        if _matches_markers(user_message, clue_markers):
            return True
    return _matches_markers(user_message, (step.player_observation, step.npc_hint))


def _matched_wrong_hypothesis(quest: QuestRule, user_message: str) -> WrongHypothesis | None:
    best_match: WrongHypothesis | None = None
    best_score = 0
    for hypothesis in quest.wrong_hypotheses:
        score = _wrong_hypothesis_score(user_message, hypothesis.text)
        if score > best_score:
            best_match = hypothesis
            best_score = score
    return best_match if best_score >= 3 else None


def _matches_wrong_hypothesis_text(user_message: str, hypothesis_text: str) -> bool:
    return _wrong_hypothesis_score(user_message, hypothesis_text) >= 3


def _wrong_hypothesis_score(user_message: str, hypothesis_text: str) -> int:
    message_tokens = _meaningful_tokens(user_message)
    hypothesis_tokens = _meaningful_tokens(hypothesis_text)
    if len(hypothesis_tokens) < 3:
        return 0
    return len(message_tokens & hypothesis_tokens)


def _step_markers(rule_set: QuestRuleSet, step: QuestStep) -> tuple[str, ...]:
    markers = [step.objective, step.player_observation, step.npc_hint, step.next_step_condition]
    markers.extend(rule_set.clues[clue_id].name for clue_id in step.unlocked_clue_ids if clue_id in rule_set.clues)
    markers.extend(step.unlocked_clue_ids)
    return tuple(markers)


def _text_markers(text: str) -> tuple[str, ...]:
    return tuple(part for part in re.split(r"[\s,./]+", text) if len(part) >= 2) + (text,)


def _matches_markers(user_message: str, markers: tuple[str, ...]) -> bool:
    normalized = _normalize(user_message)
    for marker in markers:
        normalized_marker = _normalize(marker)
        if len(normalized_marker) >= 2 and normalized_marker in normalized:
            return True
        if _has_marker_token_overlap(user_message, marker):
            return True
    return False


def _has_marker_token_overlap(user_message: str, marker: str) -> bool:
    marker_tokens = _meaningful_tokens(marker)
    if len(marker_tokens) < 2:
        return False
    message_tokens = set(_meaningful_tokens(user_message))
    matched = marker_tokens & message_tokens
    return len(matched) >= 2


def _meaningful_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"[\s,./`'\"()\[\]{}:;!?]+", value.casefold())
        if len(token) >= 2 and token not in COMMON_MARKER_TOKENS
    }


def _has_final_intent(user_message: str, rule_set: QuestRuleSet, quest: QuestRule) -> bool:
    if _matches_markers(user_message, FINAL_INTENT_MARKERS):
        return True
    if _mentions_answer_truth(rule_set, quest, user_message):
        return True
    truth_names = tuple(rule_set.truths[truth_id].name for truth_id in quest.answer_truth_ids if truth_id in rule_set.truths)
    return _matches_markers(user_message, truth_names)


def _quest_state_for_observed(
    rule_set: QuestRuleSet,
    quest: QuestRule,
    observed_clue_ids: tuple[str, ...],
    current_state: str,
) -> str:
    if current_state == "solved":
        return "solved"
    if not observed_clue_ids and current_state == "not_started":
        return "not_started"
    derived_state = "in_progress"
    if all(clue_id in observed_clue_ids for clue_id in _required_before_reveal(quest)):
        derived_state = "ready_to_answer"
        return _highest_quest_state(current_state, derived_state)
    if not observed_clue_ids:
        return _highest_quest_state(current_state, derived_state)
    max_hint_level = max((rule_set.clues[clue_id].hint_level for clue_id in observed_clue_ids if clue_id in rule_set.clues), default=1)
    if max_hint_level >= 2:
        derived_state = "hint_2_given"
        return _highest_quest_state(current_state, derived_state)
    if max_hint_level >= 1:
        derived_state = "hint_1_given"
    return _highest_quest_state(current_state, derived_state)


def _highest_quest_state(current_state: str, derived_state: str) -> str:
    order = {
        "not_started": 0,
        "in_progress": 1,
        "hint_1_given": 2,
        "hint_2_given": 3,
        "ready_to_answer": 4,
        "solved": 5,
    }
    return current_state if order.get(current_state, 1) >= order.get(derived_state, 1) else derived_state


def _all_pre_final_ready(quest_state_by_quest: dict[str, str]) -> bool:
    return all(quest_state_by_quest.get(quest_id) in {"ready_to_answer", "solved"} for quest_id in PRE_FINAL_QUEST_IDS)


def _first_incomplete_pre_final_quest(quest_state_by_quest: dict[str, str]) -> str | None:
    for quest_id in PRE_FINAL_QUEST_IDS:
        if quest_state_by_quest.get(quest_id) not in {"ready_to_answer", "solved"}:
            return quest_id
    return None


def _final_answer_score(
    rule_set: QuestRuleSet,
    quest: QuestRule,
    user_message: str,
    observed_clue_ids: tuple[str, ...],
) -> int:
    score = 0
    for clue_id in _required_before_reveal(quest):
        clue = rule_set.clues.get(clue_id)
        if clue is not None and _matches_markers(user_message, (clue.clue_id, clue.name)):
            score += 1
    for truth_id in quest.answer_truth_ids:
        truth = rule_set.truths.get(truth_id)
        if truth is not None and _matches_markers(user_message, (truth.truth_id, truth.name)):
            score += _required_final_score(quest)
        if _matches_markers(user_message, FINAL_TRUTH_MARKERS.get(truth_id, ())):
            score += _required_final_score(quest)
    return score


def _mentions_answer_truth(rule_set: QuestRuleSet, quest: QuestRule, user_message: str) -> bool:
    for truth_id in quest.answer_truth_ids:
        truth = rule_set.truths.get(truth_id)
        if truth is not None and _matches_markers(user_message, (truth.truth_id, truth.name)):
            return True
        if _matches_markers(user_message, FINAL_TRUTH_MARKERS.get(truth_id, ())):
            return True
    return False


def _required_final_score(quest: QuestRule) -> int:
    return max(2, (len(_required_before_reveal(quest)) + 1) // 2)


def _required_before_reveal(quest: QuestRule) -> tuple[str, ...]:
    if quest.answer_reveal_policy.can_reveal_truth_before_required_clues:
        return ()
    if quest.answer_reveal_policy.required_before_reveal:
        return quest.answer_reveal_policy.required_before_reveal
    return quest.required_clue_ids


def _can_npc_reveal(quest: QuestRule, npc_id: str) -> bool:
    policy = quest.answer_reveal_policy
    if npc_id in policy.npc_not_allowed_to_reveal:
        return False
    if policy.npc_allowed_to_reveal:
        return npc_id in policy.npc_allowed_to_reveal
    return npc_id == CHIEF_NPC_ID


def _npc_for_clue(rule_set: QuestRuleSet, fallback_quest: QuestRule, clue_id: str) -> str:
    for quest in rule_set.quests.values():
        for step in quest.steps:
            if clue_id in step.unlocked_clue_ids and step.npc_id and step.npc_id != CHIEF_NPC_ID:
                return step.npc_id
    for step in fallback_quest.steps:
        if clue_id in step.unlocked_clue_ids and step.npc_id:
            return step.npc_id
    return fallback_quest.involved_npc_ids[0] if fallback_quest.involved_npc_ids else CHIEF_NPC_ID


def _quest_for_clue(rule_set: QuestRuleSet, clue_id: str) -> str | None:
    for quest_id, quest in rule_set.quests.items():
        if quest_id == FINAL_QUEST_ID:
            continue
        if clue_id in quest.required_clue_ids:
            return quest_id
    for quest_id, quest in rule_set.quests.items():
        if quest_id == FINAL_QUEST_ID:
            continue
        for step in quest.steps:
            if clue_id in step.unlocked_clue_ids and step.npc_id:
                return quest_id
    return None


def _next_hint_guidance(rule_set: QuestRuleSet, quest: QuestRule, observed: tuple[str, ...], matched: tuple[str, ...]) -> str:
    if matched:
        clue_names = [rule_set.clues[clue_id].name for clue_id in matched if clue_id in rule_set.clues]
        return f"플레이어가 근거를 확인했습니다: {', '.join(clue_names)}. 다음 단서를 자연스럽게 안내하세요."
    for step in quest.steps:
        if any(clue_id not in observed for clue_id in step.unlocked_clue_ids):
            return f"아직 필요한 다음 조사 방향은 '{step.next_step_condition}'입니다. NPC가 아는 범위에서 이 방향으로 유도하세요."
    return "새로 확인된 단서는 없습니다. 현재 NPC가 아는 범위에서 기존 단서를 정리해 주세요."


def _clue_names(rule_set: QuestRuleSet, clue_ids: tuple[str, ...]) -> str:
    return ", ".join(rule_set.clues[clue_id].name if clue_id in rule_set.clues else clue_id for clue_id in clue_ids)


def _truth_names(rule_set: QuestRuleSet, truth_ids: tuple[str, ...]) -> str:
    return ", ".join(rule_set.truths[truth_id].name if truth_id in rule_set.truths else truth_id for truth_id in truth_ids)


def _decision(
    context: QuestTurnContext,
    quest_state: str,
    rule_set: QuestRuleSet,
    observed: set[str],
    matched: tuple[str, ...],
    route_to_npc_id: str | None,
    route_to_quest_id: str | None,
    missing: tuple[str, ...],
    disproof: tuple[str, ...],
    reveal_truth_ids: tuple[str, ...],
    guidance: str,
    reason: str,
) -> QuestDecision:
    return QuestDecision(
        npc_id=context.npc_id,
        quest_id=context.quest_id,
        quest_state=quest_state,
        allowed_hint_level=QUEST_STATE_HINT_LEVELS[quest_state],
        observed_clue_ids=tuple(sorted(observed)),
        newly_unlocked_clue_ids=matched,
        route_to_npc_id=route_to_npc_id,
        route_to_quest_id=route_to_quest_id,
        missing_clue_ids=missing,
        disproof_clue_ids=disproof,
        reveal_truth_ids=reveal_truth_ids,
        guidance=guidance,
        reason=reason,
    )


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value.casefold())
