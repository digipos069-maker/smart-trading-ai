from datetime import datetime, timezone
from typing import Any

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - depends on local trading terminal setup
    mt5 = None

from app.schemas.market import CandleResponse

SUPPORTED_SYMBOLS = {"XAUUSD", "EURUSD", "GBPUSD", "BTCUSD", "NQ"}
SUPPORTED_TIMEFRAMES = {"M1", "M5", "M15", "H1", "H4", "D1"}


class MT5ConnectionError(RuntimeError):
    pass


class MT5DataError(RuntimeError):
    pass


def _timeframe_map() -> dict[str, Any]:
    if mt5 is None:
        return {}

    return {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }


def validate_symbol(symbol: str) -> str:
    normalized = symbol.upper()
    if normalized not in SUPPORTED_SYMBOLS:
        supported = ", ".join(sorted(SUPPORTED_SYMBOLS))
        raise ValueError(f"Unsupported symbol '{symbol}'. Supported symbols: {supported}")
    return normalized


def validate_timeframe(timeframe: str) -> str:
    normalized = timeframe.upper()
    if normalized not in SUPPORTED_TIMEFRAMES:
        supported = ", ".join(sorted(SUPPORTED_TIMEFRAMES))
        raise ValueError(
            f"Unsupported timeframe '{timeframe}'. Supported timeframes: {supported}"
        )
    return normalized


def initialize_mt5() -> None:
    if mt5 is None:
        raise MT5ConnectionError("MetaTrader5 package is not installed.")

    if not mt5.initialize():
        code, message = mt5.last_error()
        raise MT5ConnectionError(f"Failed to initialize MetaTrader5: {code} {message}")


def get_market_status() -> dict[str, str]:
    if mt5 is None:
        return {"provider": "mt5", "status": "package_not_installed"}

    if not mt5.initialize():
        return {"provider": "mt5", "status": "not_connected"}

    return {"provider": "mt5", "status": "connected"}


def get_candles(symbol: str, timeframe: str, limit: int = 500) -> list[CandleResponse]:
    normalized_symbol = validate_symbol(symbol)
    normalized_timeframe = validate_timeframe(timeframe)

    if limit < 1 or limit > 5000:
        raise ValueError("Limit must be between 1 and 5000.")

    initialize_mt5()

    selected = mt5.symbol_select(normalized_symbol, True)
    if not selected:
        code, message = mt5.last_error()
        raise MT5DataError(
            f"Symbol '{normalized_symbol}' is not available in MetaTrader5: {code} {message}"
        )

    rates = mt5.copy_rates_from_pos(
        normalized_symbol,
        _timeframe_map()[normalized_timeframe],
        0,
        limit,
    )
    if rates is None:
        code, message = mt5.last_error()
        raise MT5DataError(f"Failed to fetch candles from MetaTrader5: {code} {message}")

    candles: list[CandleResponse] = []
    for rate in rates:
        candles.append(
            CandleResponse(
                time=datetime.fromtimestamp(int(rate["time"]), tz=timezone.utc),
                open=float(rate["open"]),
                high=float(rate["high"]),
                low=float(rate["low"]),
                close=float(rate["close"]),
                tick_volume=int(rate["tick_volume"]),
                spread=int(rate["spread"]),
            )
        )

    return candles
