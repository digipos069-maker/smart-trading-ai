from typing import Annotated
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.schemas.market import MarketDataResponse, MarketSyncRequest, MarketSyncResponse
from app.services.candle_service import save_candles
from app.services.market_data_service import (
    MarketDataProviderError,
    get_candles,
    get_market_status,
    validate_symbol,
    validate_timeframe,
)
from app.services.market_sync_service import sync_candles
from app.services.mt5_service import (
    MT5ConnectionError,
    MT5DataError,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status")
def market_status(provider: str | None = None) -> dict[str, str]:
    try:
        return get_market_status(provider)
    except MarketDataProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("/candles", response_model=MarketDataResponse)
def market_candles(
    db: Annotated[Session, Depends(get_db)],
    symbol: Annotated[str, Query(description="Trading symbol")] = "XAUUSD",
    timeframe: Annotated[str, Query(description="Timeframe")] = "M15",
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
    provider: str | None = None,
) -> MarketDataResponse:
    try:
        normalized_symbol = validate_symbol(symbol, provider)
        normalized_timeframe = validate_timeframe(timeframe, provider)
        candles = get_candles(normalized_symbol, normalized_timeframe, limit, provider)
        saved_candles = save_candles(
            db,
            candles,
            normalized_symbol,
            normalized_timeframe,
            validate_inputs=False,
        )
    except (ValueError, MarketDataProviderError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except (MT5ConnectionError, MT5DataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to persist market candles.")
        detail = "Failed to persist market candles."
        if settings.ENVIRONMENT == "development":
            detail = f"{detail} Database error: {exc}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from exc

    return MarketDataResponse(
        provider=provider or settings.MARKET_DATA_PROVIDER,
        symbol=normalized_symbol,
        timeframe=normalized_timeframe,
        count=len(saved_candles),
        candles=saved_candles,
    )


@router.post("/sync", response_model=MarketSyncResponse)
def market_sync(
    request: MarketSyncRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MarketSyncResponse:
    return sync_candles(db, request)
