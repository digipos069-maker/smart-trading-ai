import asyncio
import logging
from datetime import datetime, timezone

import requests

from app.core.config import settings
from app.database.session import SessionLocal
from app.services.candle_service import get_saved_candles
from app.services.execution_service import TradeValidationError, TradingDisabledError, execute_ict_signal
from app.services.ict_engine import analyze_ict_setup
from app.services.telegram_service import send_telegram_message

logger = logging.getLogger(__name__)

_last_alert_keys: set[str] = set()


async def run_signal_alert_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(run_signal_alert_scan)
        except Exception:
            logger.exception("Signal alert scan failed.")

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=settings.SIGNAL_ALERT_INTERVAL_SECONDS,
            )
        except asyncio.TimeoutError:
            continue


def run_signal_alert_scan() -> None:
    if not settings.SIGNAL_ALERTS_ENABLED:
        return

    symbols = _split_csv(settings.SIGNAL_ALERT_SYMBOLS)
    timeframes = _split_csv(settings.SIGNAL_ALERT_TIMEFRAMES)
    _sync_market_data(symbols, timeframes)

    with SessionLocal() as db:
        for symbol in symbols:
            for timeframe in timeframes:
                candles = get_saved_candles(
                    db,
                    symbol,
                    timeframe,
                    settings.SIGNAL_ALERT_CANDLE_LIMIT,
                )
                if len(candles) < 50:
                    continue

                analysis = analyze_ict_setup(candles, symbol.upper(), timeframe.upper())
                if analysis.score < settings.SIGNAL_ALERT_MIN_SCORE:
                    continue
                if analysis.bias not in {"bullish", "bearish"}:
                    continue

                signal_time = candles[-1].time.isoformat()
                alert_key = f"{symbol}:{timeframe}:{signal_time}:{analysis.bias}:{analysis.score}"
                if alert_key in _last_alert_keys:
                    continue

                send_telegram_message(_format_signal_message(analysis, signal_time))
                _last_alert_keys.add(alert_key)

                if settings.AUTO_EXECUTE_SIGNALS:
                    try:
                        execution = execute_ict_signal(db, analysis)
                        send_telegram_message(
                            "Smart Trading AI Execution\n"
                            f"Symbol: {execution.symbol}\n"
                            f"Direction: {execution.direction.upper()}\n"
                            f"Volume: {execution.volume}\n"
                            f"Status: {execution.status}\n"
                            f"Order: {execution.mt5_order}\n"
                            f"Message: {execution.message}"
                        )
                    except (TradeValidationError, TradingDisabledError) as exc:
                        logger.warning("Automatic signal execution skipped: %s", exc)
                        send_telegram_message(f"Smart Trading AI execution skipped: {exc}")
                    except Exception as exc:
                        logger.exception("Automatic signal execution failed.")
                        send_telegram_message(f"Smart Trading AI execution failed: {exc}")


def _sync_market_data(symbols: list[str], timeframes: list[str]) -> None:
    if not settings.MARKET_DATA_SERVICE_URL:
        return

    payload = {
        "provider": settings.SIGNAL_ALERT_SYNC_PROVIDER,
        "symbols": symbols,
        "timeframes": timeframes,
        "limit": settings.SIGNAL_ALERT_CANDLE_LIMIT,
        "notify_on_error": True,
    }
    try:
        requests.post(
            f"{settings.MARKET_DATA_SERVICE_URL.rstrip('/')}/market/sync",
            json=payload,
            timeout=30,
        ).raise_for_status()
    except requests.RequestException:
        logger.exception("Failed to sync market data before signal scan.")


def _format_signal_message(analysis, signal_time: str) -> str:
    return (
        "Smart Trading AI Signal Alert\n"
        f"Time: {datetime.now(timezone.utc).isoformat()}\n"
        f"Signal candle: {signal_time}\n"
        f"Symbol: {analysis.symbol}\n"
        f"Timeframe: {analysis.timeframe}\n"
        f"Bias: {analysis.bias.upper()}\n"
        f"Score: {analysis.score}\n"
        f"Setup: {analysis.setup_type}\n"
        f"Entry zone: {analysis.entry_zone}\n"
        f"Stop loss: {analysis.stop_loss}\n"
        f"Take profit: {analysis.take_profit}\n"
        "Warning: Educational decision support only. "
        "Backtests and signals do not guarantee future performance."
    )


def _split_csv(value: str) -> list[str]:
    return [item.strip().upper() for item in value.split(",") if item.strip()]
