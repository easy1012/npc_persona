from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.game_service.models import Account, BrowserSession, Player, Save
from src.game_service.security import hash_session_token
from src.game_service.services.account_service import AccountConflictError, convert_guest_account
from src.game_service.services.session_service import IssuedSession


class FakeScalarResult:
    def __init__(self, rows: list[Save]) -> None:
        self._rows: list[Save] = rows

    def all(self) -> list[Save]:
        return self._rows


def make_account_session(
    *,
    scalar_results: list[object | None],
    player: Player | None = None,
    saves: list[Save] | None = None,
) -> tuple[AsyncSession, list[object], AsyncMock]:
    db = AsyncSession()
    added: list[object] = []
    commit = AsyncMock()
    setattr(db, "scalar", AsyncMock(side_effect=scalar_results))
    setattr(db, "scalars", AsyncMock(return_value=FakeScalarResult(saves or [])))
    setattr(db, "get", AsyncMock(return_value=player))
    setattr(db, "add", Mock(side_effect=added.append))
    setattr(db, "commit", commit)
    return db, added, commit


class ConvertGuestAccountTests(IsolatedAsyncioTestCase):
    async def test_rejects_existing_normalized_email_without_transferring_saves_or_issuing_session(self) -> None:
        # Given: a guest session, an existing account for the normalized email, and a guest save.
        guest_player_id = uuid4()
        existing_player_id = uuid4()
        token = "guest-token"
        browser_session = BrowserSession(
            player_id=guest_player_id,
            token_hash=hash_session_token(token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        existing_account = SimpleNamespace(player_id=existing_player_id)
        guest_save = Save(player_id=guest_player_id, slot_index=0, is_current=True)
        db, _, commit = make_account_session(scalar_results=[browser_session, existing_account, 0], saves=[guest_save])

        with patch("src.game_service.services.account_service.rotate_session_after_conversion") as rotate_session:
            # When / Then: conversion fails before mutating saves or issuing a session.
            with self.assertRaises(AccountConflictError):
                _ = await convert_guest_account(db, token, " Existing@Example.COM ", "secure-password")

        self.assertEqual(guest_player_id, guest_save.player_id)
        self.assertEqual(0, guest_save.slot_index)
        self.assertTrue(guest_save.is_current)
        self.assertIsNone(browser_session.revoked_at)
        commit.assert_not_awaited()
        rotate_session.assert_not_called()

    async def test_converts_guest_to_new_normalized_email_and_rotates_session(self) -> None:
        # Given: an active guest session and no existing account for the normalized email.
        guest_player_id = uuid4()
        token = "guest-token"
        player = Player(id=guest_player_id, kind="guest")
        browser_session = BrowserSession(
            player_id=guest_player_id,
            token_hash=hash_session_token(token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db, added, commit = make_account_session(scalar_results=[browser_session, None], player=player)
        issued = IssuedSession(token="rotated-token", token_hash="rotated-hash")

        with patch("src.game_service.services.account_service.rotate_session_after_conversion", return_value=issued) as rotate_session:
            # When: the guest converts to a new email.
            player_id, rotated = await convert_guest_account(db, token, " New@Example.COM ", "secure-password")

        # Then: an account is created, the guest session is revoked, and a new session is issued.
        self.assertEqual(guest_player_id, player_id)
        self.assertEqual(issued, rotated)
        self.assertEqual("account", player.kind)
        self.assertIsNotNone(player.converted_at)
        self.assertIsNotNone(browser_session.revoked_at)
        commit.assert_awaited_once_with()
        rotate_session.assert_called_once_with()
        created_account = next(instance for instance in added if isinstance(instance, Account))
        self.assertEqual(guest_player_id, created_account.player_id)
        self.assertEqual("new@example.com", created_account.email)
        created_session = next(instance for instance in added if isinstance(instance, BrowserSession))
        self.assertEqual(guest_player_id, created_session.player_id)
        self.assertEqual("rotated-hash", created_session.token_hash)
