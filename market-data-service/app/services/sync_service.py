from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.market import MarketSyncRequest, MarketSyncResponse, MarketSyncTaskResult
from app.services.candle_service import save_candles
from app.services.market_data_service import get_candles
from app.services.telegram_service import send_telegram_message


def sync_candles(db: Session, request: MarketSyncRequest) -> MarketSyncResponse:
    provider = request.provider or settings.MARKET_DATA_PROVIDER
    results: list[MarketSyncTaskResult] = []
    total_saved = 0

    for symbol in request.symbols:
        for timeframe in request.timeframes:
            try:
                normalized_symbol, normalized_timeframe, candles = get_candles(
                    symbol,
                    timeframe,
                    request.limit,
                    provider,
                )
                saved = save_candles(db, candles, normalized_symbol, normalized_timeframe)
                total_saved += len(saved)
                results.append(
                    MarketSyncTaskResult(
                        provider=provider,
                        symbol=normalized_symbol,
                        timeframe=normalized_timeframe,
                        fetched_count=len(candles),
                        saved_count=len(saved),
                        latest_time=saved[-1].time if saved else None,
                        status="success",
                    )
                )
            except Exception as exc:
                db.rollback()
                error = str(exc)
                result = MarketSyncTaskResult(
                    provider=provider,
                    symbol=symbol.upper(),
                    timeframe=timeframe.upper(),
                    fetched_count=0,
                    saved_count=0,
                    latest_time=None,
                    status="failed",
                    error=error,
                )
                results.append(result)
                if request.notify_on_error:
                    send_telegram_message(
                        "Market data sync failed\n"
                        f"Provider: {provider}\n"
                        f"Symbol: {symbol}\n"
                        f"Timeframe: {timeframe}\n"
                        f"Error: {error}"
                    )

    return MarketSyncResponse(
        provider=provider,
        total_tasks=len(results),
        total_saved=total_saved,
        results=results,
    )
