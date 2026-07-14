from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Final
from uuid import uuid4

import requests
import streamlit as st

from src.streamlit.api_client import ChatMessage, GameApiClient, QuestProgress
from src.streamlit.journal_showcase_assets import LETTER_SVG
from src.streamlit.player_components import (
    NpcNavigatorItem,
    QuestDisclosureItem,
    render_npc_navigator,
    render_quest_disclosure,
)
from src.streamlit.quest_types import NPC_METADATA, NPC_NAMES, NPC_OPTIONS


STYLE_PATH: Final[Path] = Path(__file__).with_name("journal_showcase_styles.css")

ROLE_LABELS: Final[dict[str, str]] = {
    "farmer": "버섯밭 이웃",
    "knight": "마을 순찰대",
    "mage": "연구탑 마법사",
    "lord": "마을 회관",
}

QUEST_LABELS: Final[dict[str, str]] = {
    "q_glowing_mushroom": "빛나는 버섯의 흔적",
    "q_pig_escape": "달아난 돼지 추적",
    "q_jelly_color": "젤리의 빛깔 연구",
    "q_changed_signpost": "바뀐 표지판",
    "q_main_spore_night": "포자의 밤",
}

QUEST_STATE_LABELS: Final[dict[str, str]] = {
    "not_started": "시작 전",
    "in_progress": "조사 중",
    "hint_1_given": "첫 단서 확인",
    "hint_2_given": "두 번째 단서 확인",
    "ready_to_answer": "결론 준비",
    "solved": "해결 완료",
}


@dataclass(frozen=True, slots=True)
class PlayerView:
    npc_id: str
    npc_name: str
    quest_id: str
    messages: tuple[ChatMessage, ...]
    quests: tuple[QuestProgress, ...]


def game_api() -> GameApiClient:
    if "game_api" not in st.session_state:
        client = GameApiClient()
        client.bootstrap()
        st.session_state.game_api = client
    return st.session_state.game_api


def active_npc_id() -> str:
    query_npc_id = st.query_params.get("active_npc_id")
    if query_npc_id in NPC_OPTIONS:
        st.session_state.active_npc_id = query_npc_id
    if st.session_state.get("active_npc_id") not in NPC_OPTIONS:
        st.session_state.active_npc_id = NPC_OPTIONS[0]
    return str(st.session_state.active_npc_id)


def navigator_items(selected_npc_id: str) -> tuple[NpcNavigatorItem, ...]:
    return tuple(
        NpcNavigatorItem(
            npc_id=npc_id,
            name=NPC_NAMES[npc_id],
            role=ROLE_LABELS[NPC_METADATA[npc_id].player_role],
            quest=QUEST_LABELS[NPC_METADATA[npc_id].quest_id],
            active=npc_id == selected_npc_id,
        )
        for npc_id in NPC_OPTIONS
    )


def quest_items(quests: tuple[QuestProgress, ...]) -> tuple[QuestDisclosureItem, ...]:
    return tuple(
        QuestDisclosureItem(
            title=QUEST_LABELS[quest.quest_id],
            state=QUEST_STATE_LABELS[quest.quest_state],
            hint=f"힌트 단계 {quest.allowed_hint_level}",
        )
        for quest in quests
    )


def status_html(view: PlayerView) -> str:
    role_label = ROLE_LABELS[NPC_METADATA[view.npc_id].player_role]
    return dedent(
        f"""
        <header class="player-status" aria-labelledby="journal-title">
          <div class="status-identity">
            <span class="status-seal" aria-hidden="true">{escape(view.npc_name[:1])}</span>
            <span>
              <span class="journal-eyebrow">Hazel Village · Correspondence Log</span>
              <span class="status-role">{escape(role_label)}</span>
            </span>
          </div>
          <div class="status-copy">
            <h1 id="journal-title">{escape(view.npc_name)}</h1>
            <p class="objective-ribbon">
              <span class="objective-mark" aria-hidden="true">◆</span>
              <span><strong>현재 목표</strong>{escape(QUEST_LABELS[view.quest_id])}</span>
            </p>
            <span class="journal-online"><span aria-hidden="true"></span> 수첩 연결됨</span>
          </div>
        </header>
        """
    ).strip()


def message_html(role: str, content: str, npc_name: str) -> str:
    is_player = role == "user"
    bubble_class = "conversation-bubble is-player" if is_player else "conversation-bubble is-npc"
    speaker = "모험가" if is_player else npc_name
    meta = "수첩 답장" if is_player else "마을 서신"
    copy = escape(content).replace("\n", "<br />")
    return dedent(
        f"""
        <article class="{bubble_class}">
          <p class="bubble-speaker">{escape(speaker)}</p>
          <p class="bubble-meta">{meta}</p>
          <p class="bubble-copy">{copy}</p>
        </article>
        """
    ).strip()


def render_messages(messages: tuple[ChatMessage, ...], npc_name: str) -> str:
    if not messages:
        return dedent(
            f"""
            <article class="state-card is-empty">
              <span class="state-icon">{LETTER_SVG}</span>
              <h3>빈 대화</h3>
              <p class="state-copy">{escape(npc_name)}에게 아직 도착한 서신이 없습니다.
                <span class="keep-together">첫 이야기를</span>
                <span class="keep-together">건네 보세요.</span></p>
            </article>
            """
        ).strip()
    return "".join(message_html(message.role, message.content, npc_name) for message in messages)


def dialogue_html(view: PlayerView) -> str:
    return dedent(
        f"""
        <section class="journal-panel dialogue-panel" aria-labelledby="dialogue-title">
          <div class="panel-heading">
            <span>
              <span class="journal-eyebrow">Conversation Archive</span>
              <h2 id="dialogue-title">{escape(view.npc_name)}와의 편지</h2>
            </span>
            <span class="dialogue-count" aria-label="기록된 편지 {len(view.messages)}개">
              <span aria-hidden="true">✦</span> 기록 {len(view.messages)}
            </span>
          </div>
          <div class="bubble-stack">{render_messages(view.messages, view.npc_name)}</div>
        </section>
        """
    ).strip()


def quest_empty_html() -> str:
    return dedent(
        f"""
        <article class="state-card is-empty">
          <span class="state-icon">{LETTER_SVG}</span>
          <h3>의뢰 기록 없음</h3>
          <p class="state-copy">아직 시작한 의뢰가 없습니다.
            <span class="keep-together">대화를 보내면</span>
            이곳에 <span class="keep-together">진행 기록이 남습니다.</span></p>
        </article>
        """
    ).strip()


def quest_heading_html() -> str:
    return dedent(
        """
        <div class="panel-heading quest-heading">
          <span>
            <span class="journal-eyebrow">Quest Journal</span>
            <h2>의뢰 수첩</h2>
          </span>
          <span class="quest-compass" aria-hidden="true">✦</span>
        </div>
        """
    ).strip()


def composer_html(view: PlayerView) -> str:
    return dedent(
        f"""
        <div class="composer-legend">
          <span class="composer-quill" aria-hidden="true">✎</span>
          <span>
            <strong>{escape(view.npc_name)}에게 답장하기</strong>
            <small>Enter 전송 · Shift + Enter 줄바꿈</small>
          </span>
          <span class="composer-status"><span aria-hidden="true"></span> 전송 준비</span>
        </div>
        """
    ).strip()


def error_html() -> str:
    return dedent(
        """
        <main class="journal-showcase player-surface" aria-labelledby="journal-title">
          <header class="player-status">
            <span class="journal-eyebrow">Hazel Village Correspondence</span>
            <h1 id="journal-title">마을 통신 수첩</h1>
          </header>
          <article class="state-card is-error" role="alert">
            <h2>기록 보관소 연결 실패</h2>
            <p class="state-copy">마을 기록 보관소에 연결하지 못했습니다.
              잠시 뒤 다시 시도해 주세요.</p>
          </article>
        </main>
        """
    ).strip()


def render_player_surface(view: PlayerView, client: GameApiClient) -> None:
    with st.container(key="player-surface"):
        with st.container(key="player-navigator"):
            selected_npc_id = render_npc_navigator(navigator_items(view.npc_id))
            if selected_npc_id in NPC_OPTIONS and selected_npc_id != view.npc_id:
                st.session_state.active_npc_id = selected_npc_id
                st.query_params["active_npc_id"] = selected_npc_id
                st.rerun()

        with st.container(key="player-status"):
            _ = st.html(status_html(view))

        with st.container(key="player-dialogue"):
            _ = st.html(dialogue_html(view))

        with st.container(key="player-quest"):
            _ = st.html(quest_heading_html())
            items = quest_items(view.quests)
            if items:
                render_quest_disclosure(items)
            else:
                _ = st.html(quest_empty_html())

        dialogue_column = st.container(key="player-composer")
        with dialogue_column:
            _ = st.html(composer_html(view))
            if user_message := st.chat_input(
                f"{view.npc_name}에게 말을 건넵니다",
                key=f"player-message-{view.npc_id}",
            ):
                try:
                    client.create_turn(
                        npc_id=view.npc_id,
                        quest_id=view.quest_id,
                        content=user_message,
                        idempotency_key=uuid4().hex,
                    )
                except requests.RequestException:
                    _ = st.error("서신을 전달하지 못했습니다. 내용은 유지되며 다시 시도할 수 있습니다.")
                else:
                    st.rerun()


def render_player_app() -> None:
    _ = st.set_page_config(page_title="헤이즐 마을 통신 수첩", page_icon=None, layout="wide")
    _ = st.html(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>")
    npc_id = active_npc_id()
    try:
        client = game_api()
        conversation = client.get_conversation(npc_id)
        quests = client.get_quest_progress()
    except requests.RequestException:
        _ = st.html(error_html())
        return

    render_player_surface(
        PlayerView(
            npc_id=npc_id,
            npc_name=NPC_NAMES[npc_id],
            quest_id=NPC_METADATA[npc_id].quest_id,
            messages=conversation.messages,
            quests=quests,
        ),
        client,
    )


render_player_app()
