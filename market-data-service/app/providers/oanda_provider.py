from datetime import datetime, timezone

import requests

from app.core.config import settings
from app.schemas.market import CandleResponse
from app.providers.base import ProviderStatus

OANDA_SYMBOLS = {
    "XAUUSD",
    "XAU_USD",
    "EURUSD",
    "EUR_USD",
    "GBPUSD",
    "GBP_USD",
    "BTCUSD",
    "BTC_USD",
    "NQ",
    "NAS100_USD",
}
OANDA_SYMBOL_MAP = {
    "XAUUSD": "XAU_USD",
    "EURUSD": "EUR_USD",
    "GBPUSD": "GBP_USD",
    "BTCUSD": "BTC_USD",
    "NQ": "NAS100_USD",
}
OANDA_TIMEFRAMES = {
    "M1": "M1",
    "M5": "M5",
    "M15": "M15",
    "M30": "M30",
    "H1": "H1",
    "H4": "H4",
    "D1": "D",
}


class OandaMarketDataProvider:
    name = "oanda"

    def status(self) -> ProviderStatus:
        if not settings.OANDA_API_TOKEN:
            return {
                "provider": self.name,
                "status": "not_configured",
                "message": "Set OANDA_API_TOKEN before using OANDA market data.",
            }
        return {"provider": self.name, "status": "configured", "server": settings.OANDA_BASE_URL}

    def validate_symbol(self, symbol: str) -> str:
        normalized = symbol.upper()
        if normalized not in OANDA_SYMBOLS:
            supported = ", ".join(sorted(OANDA_SYMBOLS))
            raise ValueError(f"Unsupported OANDA symbol '{symbol}'. Supported: {supported}")
        return OANDA_SYMBOL_MAP.get(normalized, normalized)

    def validate_timeframe(self, timeframe: str) -> str:
        normalized = timeframe.upper()
        if normalized not in OANDA_TIMEFRAMES:
            supported = ", ".join(sorted(OANDA_TIMEFRAMES))
            raise ValueError(f"Unsupported OANDA timeframe '{timeframe}'. Supported: {supported}")
        return normalized

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> list[CandleResponse]:
        if not settings.OANDA_API_TOKEN:
            raise ValueError("OANDA_API_TOKEN is required for OANDA candles.")

        normalized_symbol = self.validate_symbol(symbol)
        normalized_timeframe = self.validate_timeframe(timeframe)
        if limit < 1 or limit > 5000:
            raise ValueError("OANDA candle limit must be between 1 and 5000.")

        try:
            response = requests.get(
                f"{settings.OANDA_BASE_URL}/v3/instruments/{normalized_symbol}/candles",
                headers={"Authorization": f"Bearer {settings.OANDA_API_TOKEN}"},
                params={
                    "count": limit,
                    "price": "M",
                    "granularity": OANDA_TIMEFRAMES[normalized_timeframe],
                },
                timeout=settings.MARKET_DATA_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise ValueError(f"Failed to fetch OANDA candles: {exc}") from exc

        return [
            CandleResponse(
                time=_parse_oanda_time(row["time"]),
                open=float(row["mid"]["o"]),
                high=float(row["mid"]["h"]),
                low=float(row["mid"]["l"]),
                close=float(row["mid"]["c"]),
                tick_volume=int(row.get("volume", 0)),
                spread=0,
            )
            for row in payload.get("candles", [])
            if "mid" in row
        ]


def _parse_oanda_time(value: str) -> datetime:
    if "." in value:
        prefix, suffix = value.rstrip("Z").split(".", maxsplit=1)
        value = f"{prefix}.{suffix[:6]}+00:00"
    else:
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value).astimezone(timezone.utc)
