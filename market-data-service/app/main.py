from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import market
from app.core.config import settings
from app.database.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    if settings.AUTO_CREATE_TABLES:
        init_db()
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.include_router(market.router, prefix="/market", tags=["market"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "market-data"}
