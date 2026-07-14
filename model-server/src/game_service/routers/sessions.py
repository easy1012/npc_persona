from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.game_service.db import database_session
from src.game_service.services.session_service import bootstrap_session


router = APIRouter(prefix="/sessions", tags=["sessions"])


class BootstrapResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    player_id: UUID
    save_id: UUID


@router.post("/bootstrap", response_model=BootstrapResponse)
async def bootstrap(
    response: Response,
    db: Annotated[AsyncSession, Depends(database_session)],
    hazel_session: Annotated[str | None, Cookie()] = None,
) -> BootstrapResponse:
    result = await bootstrap_session(db, hazel_session)
    if result.issued is not None:
        response.set_cookie(
            key="hazel_session",
            value=result.issued.token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=30 * 24 * 60 * 60,
            path="/",
        )
    return BootstrapResponse(player_id=result.player_id, save_id=result.save_id)
