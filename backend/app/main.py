from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.api import ai, backtest, ict, market, news
from app.core.config import settings
from app.database.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    if settings.AUTO_CREATE_TABLES:
        init_db()
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(ict.router, prefix="/ict", tags=["ict"])
app.include_router(news.router, prefix="/news", tags=["news"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
