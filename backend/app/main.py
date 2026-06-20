from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, backtest, execution, ict, market, news
from app.core.config import settings
from app.database.init_db import init_db
from app.services.signal_alert_service import run_signal_alert_loop


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    if settings.AUTO_CREATE_TABLES:
        init_db()
    stop_event = asyncio.Event()
    alert_task = None
    if settings.SIGNAL_ALERTS_ENABLED:
        alert_task = asyncio.create_task(run_signal_alert_loop(stop_event))
    yield
    stop_event.set()
    if alert_task:
        await alert_task


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(ict.router, prefix="/ict", tags=["ict"])
app.include_router(news.router, prefix="/news", tags=["news"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
app.include_router(execution.router, prefix="/execution", tags=["execution"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
