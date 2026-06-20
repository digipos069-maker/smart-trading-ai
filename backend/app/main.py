from fastapi import FastAPI

from app.api import ai, backtest, ict, market, news
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(ict.router, prefix="/api/ict", tags=["ict"])
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
