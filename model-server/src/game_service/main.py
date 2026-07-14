from __future__ import annotations

from fastapi import APIRouter, FastAPI

from src.game_service.routers.accounts import router as accounts_router
from src.game_service.routers.game import router as game_router
from src.game_service.routers.sessions import router as sessions_router


app = FastAPI(title="Hazel Village Game Service")
api_router = APIRouter(prefix="/api")
api_router.include_router(accounts_router)
api_router.include_router(game_router)
api_router.include_router(sessions_router)


@api_router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
