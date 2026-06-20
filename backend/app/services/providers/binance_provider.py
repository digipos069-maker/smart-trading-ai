from datetime import datetime, timezone
from typing import Any

import requests

from app.core.config import settings
from app.schemas.market import CandleResponse
from app.services.providers.base import ProviderStatus

BINANCE_SYMBOLS = {"BTCUSD", "BTCUSDT", "ETHUSD", "ETHUSDT", "BNBUSDT", "SOLUSDT"}
BINANCE_SYMBOL_MAP = {
    "BTCUSD": "BTCUSDT",
    "ETHUSD": "ETHUSDT",
}
BINANCE_TIMEFRAMES = {
    "M1": "1m",
    "M5": "5m",
    "M15": "15m",
    "M30": "30m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d",
}


class BinanceMarketDataProvider:
    name = "binance"

    def status(self) -> ProviderStatus:
        try:
            response = requests.get(
                f"{settings.BINANCE_BASE_URL}/api/v3/ping",
                timeout=settings.MARKET_DATA_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return {
                "provider": self.name,
                "status": "not_connected",
                "message": str(exc),
            }

        return {"provider": self.name, "status": "connected"}

    def validate_symbol(self, symbol: str) -> str:
        normalized = symbol.upper()
        if normalized not in BINANCE_SYMBOLS:
            supported = ", ".join(sorted(BINANCE_SYMBOLS))
            raise ValueError(
                f"Unsupported Binance symbol '{symbol}'. Supported symbols: {supported}"
            )
        return BINANCE_SYMBOL_MAP.get(normalized, normalized)

    def validate_timeframe(self, timeframe: str) -> str:
        normalized = timeframe.upper()
        if normalized not in BINANCE_TIMEFRAMES:
            supported = ", ".join(sorted(BINANCE_TIMEFRAMES))
            raise ValueError(
                f"Unsupported Binance timeframe '{timeframe}'. Supported timeframes: {supported}"
            )
        return normalized

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> list[CandleResponse]:
        normalized_symbol = self.validate_symbol(symbol)
        normalized_timeframe = self.validate_timeframe(timeframe)
        if limit < 1 or limit > 1000:
            raise ValueError("Binance candle limit must be between 1 and 1000.")

        try:
            response = requests.get(
                f"{settings.BINANCE_BASE_URL}/api/v3/klines",
                params={
                    "symbol": normalized_symbol,
                    "interval": BINANCE_TIMEFRAMES[normalized_timeframe],
                    "limit": limit,
                },
                timeout=settings.MARKET_DATA_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload: list[list[Any]] = response.json()
        except requests.RequestException as exc:
            raise ValueError(f"Failed to fetch Binance candles: {exc}") from exc

        return [
            CandleResponse(
                time=datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                tick_volume=int(float(row[5])),
                spread=0,
            )
            for row in payload
        ]
