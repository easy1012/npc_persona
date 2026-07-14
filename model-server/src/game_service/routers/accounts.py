from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.game_service.db import database_session
from src.game_service.services.account_service import AccountConflictError, convert_guest_account


router = APIRouter(prefix="/accounts", tags=["accounts"])


class ConvertAccountRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: EmailStr
    password: str = Field(min_length=12, max_length=256)


class ConvertAccountResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    player_id: UUID


@router.post("/convert", response_model=ConvertAccountResponse)
async def convert_account(
    request: ConvertAccountRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(database_session)],
    hazel_session: Annotated[str | None, Cookie()] = None,
) -> ConvertAccountResponse:
    if hazel_session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "guest session required")
    try:
        player_id, issued = await convert_guest_account(
            db,
            hazel_session,
            str(request.email),
            request.password,
        )
    except AccountConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    response.set_cookie(
        key="hazel_session",
        value=issued.token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
        path="/",
    )
    return ConvertAccountResponse(player_id=player_id)
