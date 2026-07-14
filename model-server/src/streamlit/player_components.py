from __future__ import annotations

import json
from typing import ClassVar, Final, TypedDict

from pydantic import BaseModel, ConfigDict
from streamlit.components import v2 as components


class NpcNavigatorItem(TypedDict):
    npc_id: str
    name: str
    role: str
    quest: str
    active: bool


class QuestDisclosureItem(TypedDict):
    title: str
    state: str
    hint: str


class _NpcNavigatorResult(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    select_npc: str | None = None


_NPC_NAVIGATOR = components.component(
    "hazel_npc_navigator",
    html='''
    <section class="roster-shell">
      <header class="roster-heading">
        <span class="kicker">Village Roster</span>
        <strong>대화 상대</strong>
        <span class="key-hint" aria-hidden="true">← →</span>
      </header>
      <nav class="npc-navigator" aria-label="대화 상대 선택"></nav>
    </section>
    ''',
    css="""
    :host {
      --ink: #2f261d;
      --muted: #6e5c49;
      --paper: #fff4d6;
      --parchment: #dbc290;
      --wood: #65492f;
      --wood-dark: #35271d;
      --moss: #436b4b;
      --honey: #c9852d;
      --berry: #8e3f3a;
      display: block;
      color: var(--ink);
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia,
        "Apple SD Gothic Neo", "Malgun Gothic", serif;
    }
    *, *::before, *::after { box-sizing: border-box; }
    .roster-shell {
      position: relative;
      padding: 1rem;
      border: 1px solid color-mix(in srgb, var(--parchment) 72%, var(--wood));
      border-radius: 1.25rem .65rem 1.1rem .75rem;
      background:
        linear-gradient(90deg, transparent 0 1.9rem, rgba(142,63,58,.16) 1.9rem 2rem, transparent 2rem),
        repeating-linear-gradient(0deg, transparent 0 1.8rem, rgba(101,73,47,.08) 1.85rem 1.9rem),
        color-mix(in srgb, var(--paper) 96%, var(--parchment));
      box-shadow: 0 1.2rem 2.5rem rgba(24,17,12,.24), inset 0 0 0 .25rem rgba(255,255,255,.24);
      overflow: hidden;
    }
    .roster-shell::after {
      content: "";
      position: absolute;
      inset: .4rem;
      border: 1px dashed rgba(101,73,47,.22);
      border-radius: .95rem .45rem .85rem .55rem;
      pointer-events: none;
    }
    .roster-heading {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: minmax(0,1fr) auto;
      align-items: end;
      gap: .1rem .75rem;
      margin: 0 0 .85rem;
      padding: .15rem .2rem .8rem 1.35rem;
      border-bottom: 1px solid rgba(101,73,47,.26);
    }
    .roster-heading::before {
      content: "";
      position: absolute;
      left: 0;
      bottom: .75rem;
      width: .65rem;
      height: 1.7rem;
      border-radius: 999px;
      background: var(--berry);
      box-shadow: 0 0 0 .2rem rgba(142,63,58,.14);
    }
    .kicker {
      grid-column: 1 / -1;
      color: var(--muted);
      font-size: .875rem;
      font-weight: 700;
      letter-spacing: .12em;
      text-transform: uppercase;
    }
    .roster-heading strong { font-size: 1.25rem; line-height: 1.2; }
    .key-hint {
      padding: .22rem .45rem;
      border: 1px solid rgba(101,73,47,.35);
      border-radius: .4rem;
      color: var(--muted);
      background: rgba(255,255,255,.28);
      font: 700 .875rem/1 sans-serif;
    }
    .npc-navigator {
      position: relative;
      z-index: 1;
      display: grid;
      gap: .75rem;
    }
    .npc-navigator::-webkit-scrollbar { height: .5rem; }
    .npc-navigator::-webkit-scrollbar-track { border-radius: 99px; background: rgba(101,73,47,.08); }
    .npc-navigator::-webkit-scrollbar-thumb {
      border: 1px solid rgba(101,73,47,.28);
      border-radius: 99px;
      background: color-mix(in srgb, var(--parchment) 80%, var(--wood));
    }
    button {
      position: relative;
      display: grid;
      grid-template-columns: 3rem minmax(0, 1fr);
      align-items: center;
      gap: .75rem;
      width: 100%;
      min-height: 5.35rem;
      padding: .8rem .85rem;
      border: 1px solid color-mix(in srgb, var(--parchment) 72%, var(--wood));
      border-left: .35rem solid var(--muted);
      border-radius: .25rem .85rem .85rem .25rem;
      background:
        linear-gradient(105deg, rgba(255,255,255,.35), transparent 52%),
        color-mix(in srgb, var(--paper) 82%, transparent);
      color: var(--ink);
      text-align: left;
      cursor: pointer;
      box-shadow: 0 .35rem .75rem rgba(47,38,29,.08);
      transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
      isolation: isolate;
    }
    button::after {
      content: "";
      position: absolute;
      top: 50%;
      right: -.1rem;
      width: .38rem;
      height: 2.4rem;
      border-radius: 99px 0 0 99px;
      background: var(--parchment);
      transform: translateY(-50%);
      opacity: .45;
    }
    button:hover {
      border-color: var(--honey);
      background-color: var(--paper);
      box-shadow: 0 .65rem 1.2rem rgba(47,38,29,.16);
      transform: translateX(.18rem);
    }
    button:focus-visible {
      outline: 3px solid var(--honey);
      outline-offset: .18rem;
      box-shadow: 0 0 0 .35rem color-mix(in srgb, var(--wood-dark) 28%, transparent), 0 .65rem 1.2rem rgba(47,38,29,.16);
    }
    button[aria-current="true"] {
      border-left-color: var(--moss);
      border-color: var(--moss);
      background:
        linear-gradient(105deg, rgba(255,255,255,.55), transparent 55%),
        color-mix(in srgb, var(--paper) 91%, var(--moss));
      box-shadow: 0 .7rem 1.25rem rgba(47,38,29,.18), inset .25rem 0 0 var(--moss);
      transform: translateX(.18rem);
    }
    button[aria-current="true"]::after {
      background: var(--moss);
      opacity: 1;
    }
    .seal {
      display: grid;
      place-items: center;
      width: 3rem;
      height: 3rem;
      border: 2px solid var(--wood);
      border-radius: 50%;
      background: color-mix(in srgb, var(--paper) 76%, var(--honey));
      box-shadow: inset 0 0 0 .25rem rgba(255,255,255,.35), 0 .18rem .35rem rgba(47,38,29,.2);
      color: var(--wood-dark);
      font-size: 1.25rem;
      font-weight: 700;
    }
    button[aria-current="true"] .seal {
      border-color: var(--moss);
      color: var(--moss);
      transform: rotate(-4deg);
    }
    .copy { min-width: 0; }
    .name { display: block; font-size: 1.02rem; font-weight: 800; line-height: 1.25; }
    .meta {
      display: block;
      margin-top: .18rem;
      overflow: hidden;
      color: var(--muted);
      font-size: .875rem;
      line-height: 1.4;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .state {
      display: inline-flex;
      align-items: center;
      gap: .35rem;
      margin-top: .42rem;
      padding: .15rem .45rem;
      border-radius: 99px;
      color: var(--muted);
      background: rgba(101,73,47,.08);
      font-size: .875rem;
      font-weight: 700;
    }
    .state::before {
      content: "";
      width: .42rem;
      height: .42rem;
      border: 1px solid currentColor;
      border-radius: 50%;
      background: transparent;
    }
    button[aria-current="true"] .state { color: var(--moss); background: rgba(67,107,75,.1); }
    button[aria-current="true"] .state::before { background: var(--moss); box-shadow: 0 0 0 .16rem rgba(67,107,75,.14); }
    @media (max-width: 1279px) {
      .roster-shell { padding: .85rem; }
      .roster-heading { grid-template-columns: minmax(0,1fr) auto; }
      .npc-navigator {
        grid-template-columns: repeat(4, minmax(14rem, 1fr));
        overflow-x: auto;
        padding: .25rem .2rem .75rem;
        scroll-snap-type: x proximity;
        scrollbar-color: var(--parchment) transparent;
      }
      button { scroll-snap-align: start; }
    }
    @media (max-width: 767px) {
      .roster-heading { padding-bottom: .65rem; }
      .npc-navigator { grid-template-columns: repeat(4, minmax(min(16rem, 82vw), 1fr)); }
      button { min-height: 5rem; }
    }
    @media (prefers-reduced-motion: reduce) {
      button { transition: none; }
    }
    """,
    js="""
    export default function({ parentElement, data, setTriggerValue }) {
      const root = parentElement.querySelector(".npc-navigator");
      root.replaceChildren();

      data.items.forEach((item) => {
        const button = document.createElement("button");
        button.type = "button";
        button.dataset.npcId = item.npc_id;
        button.setAttribute("aria-label", `${item.name} ${item.active ? "현재 대화" : "대화 열기"}`);
        if (item.active) button.setAttribute("aria-current", "true");

        const seal = document.createElement("span");
        seal.className = "seal";
        seal.setAttribute("aria-hidden", "true");
        seal.textContent = item.name.slice(0, 1);

        const copy = document.createElement("span");
        copy.className = "copy";
        const name = document.createElement("strong");
        name.className = "name";
        name.textContent = item.name;
        const meta = document.createElement("span");
        meta.className = "meta";
        meta.textContent = `${item.role} · ${item.quest}`;
        const state = document.createElement("span");
        state.className = "state";
        state.textContent = item.active ? "현재 대화" : "대화 열기";
        copy.append(name, meta, state);
        button.append(seal, copy);
        button.onclick = () => setTriggerValue("select_npc", item.npc_id);
        root.append(button);
      });
      root.querySelector('[aria-current="true"]')?.scrollIntoView({ block: "nearest", inline: "center" });

      root.onkeydown = (event) => {
        const navigationKeys = ["ArrowRight", "ArrowLeft", "ArrowDown", "ArrowUp", "Home", "End"];
        if (!navigationKeys.includes(event.key)) return;
        const buttons = Array.from(root.querySelectorAll("button"));
        const current = buttons.indexOf(root.getRootNode().activeElement);
        const nextIndex = event.key === "Home" ? 0
          : event.key === "End" ? buttons.length - 1
          : (current + (["ArrowRight", "ArrowDown"].includes(event.key) ? 1 : -1) + buttons.length) % buttons.length;
        buttons[nextIndex].focus();
        event.preventDefault();
      };
    }
    """,
)

_QUEST_DISCLOSURE = components.component(
    "hazel_quest_disclosure",
    html='<details class="quest-disclosure"><summary>의뢰 수첩 펼치기</summary><div></div></details>',
    css="""
    :host {
      --ink: #2f261d;
      --muted: #6e5c49;
      --paper: #fff4d6;
      --parchment: #dbc290;
      --wood: #65492f;
      --moss: #436b4b;
      --honey: #c9852d;
      display: block;
      color: var(--ink);
      font-family: "Iowan Old Style", Georgia, "Malgun Gothic", serif;
    }
    *, *::before, *::after { box-sizing: border-box; }
    details {
      border: 1px solid var(--wood);
      border-radius: .85rem;
      background: var(--paper);
      overflow: hidden;
    }
    summary {
      min-height: 3.25rem;
      padding: .9rem 1rem;
      color: var(--wood);
      background: linear-gradient(90deg, rgba(201,133,45,.12), transparent);
      cursor: pointer;
      font-weight: 800;
    }
    summary:focus-visible { outline: 3px solid var(--honey); outline-offset: -.2rem; }
    .quest-list { display: grid; gap: .7rem; }
    article {
      position: relative;
      margin: 0 .75rem;
      padding: .85rem .85rem .85rem 1rem;
      border: 1px solid color-mix(in srgb, var(--parchment) 80%, var(--wood));
      border-left: .3rem solid var(--moss);
      border-radius: .65rem;
      background:
        repeating-linear-gradient(0deg, transparent 0 1.7rem, rgba(101,73,47,.06) 1.75rem 1.8rem),
        rgba(255,255,255,.22);
      box-shadow: 0 .3rem .65rem rgba(47,38,29,.08);
    }
    article:first-child { margin-top: .75rem; }
    article:last-child { margin-bottom: .75rem; }
    h3, p { margin: 0; }
    h3 { padding-right: 1.5rem; font-size: 1rem; line-height: 1.35; word-break: keep-all; }
    .quest-state { margin-top: .42rem; color: var(--moss); font-size: .875rem; font-weight: 800; }
    .quest-state::before { content: "◆"; margin-right: .35rem; font-size: .65rem; }
    .hint-badge {
      display: inline-flex;
      margin-top: .55rem;
      padding: .2rem .5rem;
      border: 1px dashed var(--parchment);
      border-radius: 99px;
      color: var(--muted);
      background: rgba(219,194,144,.14);
      font-size: .875rem;
      font-weight: 700;
    }
    .quest-pin {
      position: absolute;
      top: .75rem;
      right: .75rem;
      width: .55rem;
      height: .55rem;
      border: 1px solid var(--wood);
      border-radius: 50%;
      background: var(--honey);
      box-shadow: 0 .15rem .2rem rgba(47,38,29,.25);
    }
    @media (min-width: 768px) {
      summary { display: none; }
      details { border: 0; background: transparent; overflow: visible; }
      article { margin-inline: 0; }
      article:first-child { margin-top: 0; }
      article:last-child { margin-bottom: 0; }
    }
    """,
    js="""
    export default function({ parentElement, data }) {
      const details = parentElement.querySelector("details");
      const list = parentElement.querySelector("details > div");
      list.className = "quest-list";
      const viewport = window.matchMedia("(min-width: 768px)");
      const syncDisclosure = (event) => { details.open = event.matches; };
      syncDisclosure(viewport);
      viewport.onchange = syncDisclosure;
      list.replaceChildren();
      data.items.forEach((item) => {
        const article = document.createElement("article");
        const title = document.createElement("h3");
        title.textContent = item.title;
        const state = document.createElement("p");
        state.className = "quest-state";
        state.textContent = item.state;
        const hint = document.createElement("span");
        hint.className = "hint-badge";
        hint.textContent = item.hint;
        const pin = document.createElement("span");
        pin.className = "quest-pin";
        pin.setAttribute("aria-hidden", "true");
        article.append(title, state, hint, pin);
        list.append(article);
      });
    }
    """,
)


def _accept_trigger() -> None:
    return None


def render_npc_navigator(items: tuple[NpcNavigatorItem, ...]) -> str | None:
    result = _NPC_NAVIGATOR(
        key="hazel-npc-navigator",
        data={"items": list(items)},
        width="stretch",
        height="content",
        on_select_npc_change=_accept_trigger,
    )
    payload = _NpcNavigatorResult.model_validate_json(json.dumps(result))
    return payload.select_npc


def render_quest_disclosure(items: tuple[QuestDisclosureItem, ...]) -> None:
    _ = _QUEST_DISCLOSURE(
        key="hazel-quest-disclosure",
        data={"items": list(items)},
        width="stretch",
        height="content",
    )


COMPONENT_NAMES: Final[tuple[str, str]] = (
    "hazel_npc_navigator",
    "hazel_quest_disclosure",
)
