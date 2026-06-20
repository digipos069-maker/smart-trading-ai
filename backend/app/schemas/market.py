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


class CandleFetchRequest(BaseModel):
    symbol: str = Field(..., examples=["XAUUSD"])
    timeframe: str = Field(..., examples=["M15"])
    limit: int = Field(default=500, ge=1, le=5000)


class MarketDataResponse(BaseModel):
    symbol: str
    timeframe: str
    count: int
    candles: list[CandleResponse]
