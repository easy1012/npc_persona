from __future__ import annotations

from pathlib import Path
from typing import Final

import streamlit as st

from src.streamlit.journal_showcase_assets import (
    CONVERSATION_SAMPLES,
    LETTER_SVG,
    NPC_ITEMS,
    QUEST_CLUES,
    ROUTE_SVG,
    STATE_SAMPLES,
    WARNING_SVG,
    BubbleKind,
    NpcState,
    StateKind,
    seal_svg,
)


STYLE_PATH: Final[Path] = Path(__file__).resolve().parents[1] / "journal_showcase_styles.css"


def load_styles() -> None:
    _ = st.markdown(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def roster_class(state: NpcState) -> str:
    match state:
        case "active":
            return "npc-card is-active motion-sample"
        case "unread":
            return "npc-card is-unread"
        case "route":
            return "npc-card is-route"
        case "idle":
            return "npc-card"


def badge_class(state: NpcState) -> str:
    match state:
        case "active":
            return "journal-badge"
        case "unread":
            return "journal-badge is-unread"
        case "route":
            return "journal-badge is-route"
        case "idle":
            return "journal-badge"


def bubble_class(kind: BubbleKind) -> str:
    match kind:
        case "npc":
            return "conversation-bubble is-npc"
        case "player":
            return "conversation-bubble is-player"


def state_icon(kind: StateKind) -> str:
    match kind:
        case "empty":
            return LETTER_SVG
        case "loading":
            return ROUTE_SVG
        case "error":
            return WARNING_SVG


def render_showcase() -> str:
    roster = "".join(
        f"""
        <a class="{roster_class(item.state)}" href="#dialogue" aria-label="{item.name} {item.badge}">
          <span class="npc-seal">{seal_svg(item.name)}</span>
          <span>
            <strong class="npc-name">{item.name}</strong><br />
            <span class="npc-meta">{item.role} · {item.quest_state}</span><br />
            <span class="{badge_class(item.state)}">{item.badge}</span>
          </span>
        </a>
        """
        for item in NPC_ITEMS
    )
    bubbles = "".join(
        f"""
        <article class="{bubble_class(sample.kind)}">
          <p class="bubble-speaker">{sample.speaker}</p>
          <p class="bubble-meta">{sample.meta}</p>
          <p class="bubble-copy">{sample.text}</p>
        </article>
        """
        for sample in CONVERSATION_SAMPLES
    )
    clues = "".join(
        f"""
        <div class="quest-row">
          <strong>{clue.mark}</strong>
          <span><strong>{clue.title}</strong><br /><span class="quest-copy">{clue.detail}</span></span>
        </div>
        """
        for clue in QUEST_CLUES
    )
    states = "".join(
        f"""
        <article class="state-card is-{sample.kind}">
          <span class="state-icon">{state_icon(sample.kind)}</span>
          <h3>{sample.title}</h3>
          <p class="state-copy">{sample.detail}</p>
          <button class="journal-action" type="button">동작: 확인</button>
        </article>
        """
        for sample in STATE_SAMPLES
    )
    return f"""
    <main class="journal-showcase" aria-labelledby="journal-title">
      <section class="journal-hero">
        <span class="journal-eyebrow">Hazel Village UI Contract</span>
        <h1 id="journal-title">마을 통신 수첩</h1>
        <p>왼쪽은 NPC 편지함, 가운데는 독립 대화 장부, 오른쪽은 퀘스트 단서 수첩입니다. 이 페이지는 제품 화면이 아니라 재사용할 primitive와 상태를 검증하는 독립 showcase입니다.</p>
      </section>
      <section class="journal-layout" aria-label="journal primitive layout">
        <aside class="journal-panel roster-panel" aria-labelledby="roster-title">
          <h2 id="roster-title">NPC Roster States</h2>
          <div class="roster-list">{roster}</div>
        </aside>
        <section id="dialogue" class="journal-panel" aria-labelledby="dialogue-title">
          <h2 id="dialogue-title">Conversation Bubbles</h2>
          <div class="bubble-stack">{bubbles}</div>
          <p class="journal-badge">Focus: Tab으로 NPC 카드와 버튼을 이동하면 꿀색 외곽선이 보여야 합니다.</p>
        </section>
        <aside class="journal-panel" aria-labelledby="quest-title">
          <h2 id="quest-title">Quest Journal</h2>
          <article class="quest-card">
            <p class="quest-title">빛나는 버섯과 바뀐 표지판</p>
            {clues}
            <span class="journal-badge is-route">{ROUTE_SVG} 추천 이동: 헤이즐 촌장 로완</span>
          </article>
        </aside>
      </section>
      <section class="state-grid" aria-label="empty loading error states">{states}</section>
    </main>
    """


st.set_page_config(page_title="Journal Primitive Showcase", layout="wide")
load_styles()
_ = st.markdown(render_showcase(), unsafe_allow_html=True)
