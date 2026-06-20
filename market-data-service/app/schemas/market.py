from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CandleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int


class MarketDataResponse(BaseModel):
    provider: str
    symbol: str
    timeframe: str
    count: int
    candles: list[CandleResponse]


class MarketSyncRequest(BaseModel):
    provider: str | None = None
    symbols: list[str] = Field(default_factory=lambda: ["XAUUSD"], min_length=1)
    timeframes: list[str] = Field(default_factory=lambda: ["M5"], min_length=1)
    limit: int = Field(default=500, ge=1, le=5000)
    notify_on_error: bool = True


class MarketSyncTaskResult(BaseModel):
    provider: str
    symbol: str
    timeframe: str
    fetched_count: int
    saved_count: int
    latest_time: datetime | None = None
    status: str
    error: str | None = None


class MarketSyncResponse(BaseModel):
    provider: str
    total_tasks: int
    total_saved: int
    results: list[MarketSyncTaskResult]
