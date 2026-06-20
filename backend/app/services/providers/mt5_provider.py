from app.schemas.market import CandleResponse
from app.services import mt5_service
from app.services.providers.base import ProviderStatus


class MT5MarketDataProvider:
    name = "mt5"

    def status(self) -> ProviderStatus:
        return mt5_service.get_market_status()

    def validate_symbol(self, symbol: str) -> str:
        return mt5_service.validate_symbol(symbol)

    def validate_timeframe(self, timeframe: str) -> str:
        return mt5_service.validate_timeframe(timeframe)

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> list[CandleResponse]:
        return mt5_service.get_candles(symbol, timeframe, limit)
