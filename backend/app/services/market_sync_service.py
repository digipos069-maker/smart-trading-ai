from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.candle import Candle
from app.schemas.market import MarketSyncRequest, MarketSyncResponse, MarketSyncTaskResult
from app.services.candle_service import save_candles
from app.services.market_data_service import get_candles, validate_symbol, validate_timeframe


def sync_candles(db: Session, request: MarketSyncRequest) -> MarketSyncResponse:
    provider = request.provider or settings.MARKET_DATA_PROVIDER
    tasks: list[MarketSyncTaskResult] = []
    total_saved = 0

    for symbol in request.symbols:
        for timeframe in request.timeframes:
            try:
                normalized_symbol = validate_symbol(symbol, provider)
                normalized_timeframe = validate_timeframe(timeframe, provider)
                fetched = get_candles(
                    normalized_symbol,
                    normalized_timeframe,
                    request.limit,
                    provider,
                )
                saved = save_candles(
                    db,
                    fetched,
                    normalized_symbol,
                    normalized_timeframe,
                    validate_inputs=False,
                )
                total_saved += len(saved)
                tasks.append(
                    MarketSyncTaskResult(
                        provider=provider,
                        symbol=normalized_symbol,
                        timeframe=normalized_timeframe,
                        fetched_count=len(fetched),
                        saved_count=len(saved),
                        latest_time=saved[-1].time if saved else None,
                        status="success",
                    )
                )
            except Exception as exc:
                db.rollback()
                tasks.append(
                    MarketSyncTaskResult(
                        provider=provider,
                        symbol=symbol.upper(),
                        timeframe=timeframe.upper(),
                        fetched_count=0,
                        saved_count=0,
                        latest_time=None,
                        status="failed",
                        error=str(exc),
                    )
                )

    return MarketSyncResponse(
        provider=provider,
        total_tasks=len(tasks),
        total_saved=total_saved,
        results=tasks,
    )
