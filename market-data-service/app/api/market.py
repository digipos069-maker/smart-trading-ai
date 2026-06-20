from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.market import MarketDataResponse, MarketSyncRequest, MarketSyncResponse
from app.services.candle_service import save_candles
from app.services.market_data_service import (
    MarketDataProviderError,
    get_candles,
    get_market_status,
)
from app.services.sync_service import sync_candles

router = APIRouter()


@router.get("/status")
def market_status(provider: str | None = None) -> dict[str, str]:
    try:
        return get_market_status(provider)
    except MarketDataProviderError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/candles", response_model=MarketDataResponse)
def market_candles(
    db: Annotated[Session, Depends(get_db)],
    symbol: Annotated[str, Query(description="Trading symbol")] = "XAUUSD",
    timeframe: Annotated[str, Query(description="Timeframe")] = "M5",
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
    provider: str | None = None,
) -> MarketDataResponse:
    try:
        normalized_symbol, normalized_timeframe, candles = get_candles(
            symbol,
            timeframe,
            limit,
            provider,
        )
        saved = save_candles(db, candles, normalized_symbol, normalized_timeframe)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return MarketDataResponse(
        provider=provider or "default",
        symbol=normalized_symbol,
        timeframe=normalized_timeframe,
        count=len(saved),
        candles=saved,
    )


@router.post("/sync", response_model=MarketSyncResponse)
def market_sync(
    request: MarketSyncRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MarketSyncResponse:
    return sync_candles(db, request)
