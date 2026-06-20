from app.core.config import settings
from app.providers import (
    BinanceMarketDataProvider,
    MarketDataProvider,
    MT5MarketDataProvider,
    OandaMarketDataProvider,
    ProviderStatus,
)
from app.schemas.market import CandleResponse


class MarketDataProviderError(ValueError):
    pass


def get_market_data_provider(provider_name: str | None = None) -> MarketDataProvider:
    provider = (provider_name or settings.MARKET_DATA_PROVIDER).lower()
    if provider == "mt5":
        return MT5MarketDataProvider()
    if provider == "binance":
        return BinanceMarketDataProvider()
    if provider == "oanda":
        return OandaMarketDataProvider()
    raise MarketDataProviderError(f"Unsupported market data provider '{provider}'.")


def get_market_status(provider_name: str | None = None) -> ProviderStatus:
    return get_market_data_provider(provider_name).status()


def get_candles(
    symbol: str,
    timeframe: str,
    limit: int = 500,
    provider_name: str | None = None,
) -> tuple[str, str, list[CandleResponse]]:
    provider = get_market_data_provider(provider_name)
    normalized_symbol = provider.validate_symbol(symbol)
    normalized_timeframe = provider.validate_timeframe(timeframe)
    candles = provider.get_candles(normalized_symbol, normalized_timeframe, limit)
    return normalized_symbol, normalized_timeframe, candles
