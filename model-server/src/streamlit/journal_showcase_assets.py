from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal


NpcState = Literal["active", "unread", "route", "idle"]
BubbleKind = Literal["npc", "player"]
StateKind = Literal["empty", "loading", "error"]


@dataclass(frozen=True, slots=True)
class NpcShowcaseItem:
    name: str
    role: str
    quest_state: str
    state: NpcState
    badge: str


@dataclass(frozen=True, slots=True)
class ConversationSample:
    speaker: str
    meta: str
    text: str
    kind: BubbleKind


@dataclass(frozen=True, slots=True)
class QuestClue:
    mark: str
    title: str
    detail: str


@dataclass(frozen=True, slots=True)
class StateSample:
    title: str
    detail: str
    kind: StateKind


NPC_ITEMS: Final[tuple[NpcShowcaseItem, ...]] = (
    NpcShowcaseItem("민민 부인", "버섯밭 이웃", "빛나는 버섯 조사 중", "active", "현재 대화"),
    NpcShowcaseItem("순찰대장 리오", "마을 순찰대", "돼지 탈출 단서 2개", "unread", "새 편지 2"),
    NpcShowcaseItem("마도사 루미", "연구탑 마법사", "젤리 색 변화 확인", "idle", "대기"),
    NpcShowcaseItem("헤이즐 촌장 로완", "마을 회관", "포자 밤 최종 보고", "route", "추천 이동"),
)

CONVERSATION_SAMPLES: Final[tuple[ConversationSample, ...]] = (
    ConversationSample(
        "민민 부인",
        "버섯밭 울타리 앞 · 관계: 신뢰",
        "오늘 새벽에 버섯 갓이 노랗게 반짝였어요. 표지판 쪽 흙도 같이 확인하면 길이 이어질 거예요.",
        "npc",
    ),
    ConversationSample(
        "모험가",
        "수첩 답장 · 단서 확인",
        "그럼 버섯밭에서 본 빛과 표지판 주변의 뿌리 자국을 함께 기록해 둘게요.",
        "player",
    ),
)

QUEST_CLUES: Final[tuple[QuestClue, ...]] = (
    QuestClue("I", "현재 목표", "빛나는 버섯의 색 변화와 표지판 옆 흙자국을 같은 사건으로 묶어 확인한다."),
    QuestClue("II", "관찰한 단서", "노란 포자, 젖은 발자국, 부러진 나뭇조각."),
    QuestClue("III", "허용 힌트", "힌트 2단계까지 공개. 최종 진실은 로완에게 보고하기 전까지 잠금."),
)

STATE_SAMPLES: Final[tuple[StateSample, ...]] = (
    StateSample("빈 대화", "아직 이 NPC와 나눈 편지가 없습니다. 첫 질문을 남기면 독립 대화가 시작됩니다.", "empty"),
    StateSample("불러오는 중", "마을 우편함에서 이전 편지를 정리하는 중입니다. 완료되면 같은 자리에서 이어집니다.", "loading"),
    StateSample("전송 실패", "응답을 저장하지 못했습니다. 같은 요청은 다시 시도해도 중복 기록되지 않아야 합니다.", "error"),
)


def seal_svg(label: str) -> str:
    return f"""
    <svg aria-hidden="true" viewBox="0 0 48 48" width="48" height="48" role="img">
      <circle cx="24" cy="24" r="19" fill="none" stroke="currentColor" stroke-width="3" />
      <path d="M14 28c6-12 14-12 20 0M17 18h14M18 34h12" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" />
      <title>{label}</title>
    </svg>
    """


ROUTE_SVG: Final[str] = """
<svg aria-hidden="true" viewBox="0 0 48 48" width="42" height="42" role="img">
  <path d="M8 37c6-16 14 4 20-12 3-8 7-10 12-14" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-dasharray="4 5" />
  <path d="M34 9l7 1-1 7" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
</svg>
"""

LETTER_SVG: Final[str] = """
<svg aria-hidden="true" viewBox="0 0 48 48" width="42" height="42" role="img">
  <path d="M8 14h32v23H8z" fill="none" stroke="currentColor" stroke-width="3" />
  <path d="M10 16l14 12 14-12" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" />
</svg>
"""

WARNING_SVG: Final[str] = """
<svg aria-hidden="true" viewBox="0 0 48 48" width="42" height="42" role="img">
  <path d="M24 7l18 33H6z" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round" />
  <path d="M24 18v10M24 34h.1" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
</svg>
"""
