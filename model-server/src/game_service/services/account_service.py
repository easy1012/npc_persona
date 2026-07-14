from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.game_service.models import Account, BrowserSession, Player
from src.game_service.security import hash_session_token
from src.game_service.services.session_service import IssuedSession, issue_session


def rotate_session_after_conversion() -> IssuedSession:
    return issue_session()


class AccountConflictError(Exception):
    pass


async def convert_guest_account(
    db: AsyncSession,
    session_token: str,
    email: str,
    password: str,
) -> tuple[UUID, IssuedSession]:
    browser_session = await db.scalar(
        select(BrowserSession)
        .where(
            BrowserSession.token_hash == hash_session_token(session_token),
            BrowserSession.revoked_at.is_(None),
        )
        .with_for_update()
    )
    if browser_session is None:
        raise AccountConflictError("active guest session required")

    normalized_email = email.strip().casefold()
    existing_account = await db.scalar(
        select(Account).where(Account.email == normalized_email).with_for_update()
    )
    player_id = browser_session.player_id
    if existing_account is not None:
        raise AccountConflictError("account email already exists")

    player = await db.get(Player, player_id, with_for_update=True)
    if player is None or player.kind != "guest":
        raise AccountConflictError("guest player required")
    player.kind = "account"
    player.converted_at = datetime.now(timezone.utc)
    db.add(
        Account(
            player_id=player_id,
            email=normalized_email,
            password_hash=PasswordHasher().hash(password),
        )
    )

    browser_session.revoked_at = datetime.now(timezone.utc)
    issued = rotate_session_after_conversion()
    db.add(
        BrowserSession(
            player_id=player_id,
            token_hash=issued.token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
    )
    await db.commit()
    return player_id, issued
