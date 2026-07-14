from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.game_service.models import BrowserSession, Player, Save
from src.game_service.security import generate_session_token, hash_session_token


@dataclass(frozen=True, slots=True)
class IssuedSession:
    token: str
    token_hash: str


@dataclass(frozen=True, slots=True)
class SessionBootstrap:
    player_id: UUID
    save_id: UUID
    issued: IssuedSession | None


@dataclass(frozen=True, slots=True)
class SessionPrincipal:
    player_id: UUID
    save_id: UUID


def issue_session() -> IssuedSession:
    token = generate_session_token()
    token_hash = hash_session_token(token)
    return IssuedSession(token, token_hash)


async def resolve_session(db: AsyncSession, presented_token: str) -> SessionPrincipal | None:
    browser_session = await db.scalar(
        select(BrowserSession).where(
            BrowserSession.token_hash == hash_session_token(presented_token),
            BrowserSession.revoked_at.is_(None),
            BrowserSession.expires_at > datetime.now(timezone.utc),
        )
    )
    if browser_session is None:
        return None
    save_id = await db.scalar(
        select(Save.id).where(
            Save.player_id == browser_session.player_id,
            Save.is_current.is_(True),
        )
    )
    if save_id is None:
        return None
    return SessionPrincipal(browser_session.player_id, save_id)


async def bootstrap_session(db: AsyncSession, presented_token: str | None) -> SessionBootstrap:
    if presented_token:
        principal = await resolve_session(db, presented_token)
        if principal is not None:
            return SessionBootstrap(principal.player_id, principal.save_id, None)

    issued = issue_session()
    player = Player(kind="guest")
    db.add(player)
    await db.flush()
    save = Save(player_id=player.id)
    browser_session = BrowserSession(
        player_id=player.id,
        token_hash=issued.token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add_all([save, browser_session])
    await db.commit()
    return SessionBootstrap(player.id, save.id, issued)
