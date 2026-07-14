from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from src.streamlit.quest_rules import evaluate_quest_turn
from src.streamlit.quest_types import QuestGraphState, QuestRuleSet, QuestTurnContext


def build_quest_graph(rule_set: QuestRuleSet):
    builder = StateGraph(QuestGraphState)

    def evaluate_node(state: QuestGraphState) -> QuestGraphState:
        context = QuestTurnContext(
            npc_id=state["npc_id"],
            quest_id=state["quest_id"],
            user_message=state["user_message"],
            quest_state_by_quest=state["quest_state_by_quest"],
            observed_clue_ids_by_quest={
                quest_id: tuple(clue_ids)
                for quest_id, clue_ids in state["observed_clue_ids_by_quest"].items()
            },
        )
        decision = evaluate_quest_turn(rule_set, context)
        updated_observed = dict(state["observed_clue_ids_by_quest"])
        updated_observed[decision.quest_id] = list(decision.observed_clue_ids)
        return {
            **state,
            "observed_clue_ids_by_quest": updated_observed,
            "decision": decision.as_record(),
        }

    builder.add_node("evaluate_quest_turn", evaluate_node)
    builder.add_edge(START, "evaluate_quest_turn")
    builder.add_edge("evaluate_quest_turn", END)
    return builder.compile(checkpointer=InMemorySaver())
