from typing import Protocol, TypedDict

from app.schemas.market import CandleResponse


class ProviderStatus(TypedDict, total=False):
    provider: str
    status: str
    message: str
    error_code: str
    account: str
    server: str
    terminal_path: str


class MarketDataProvider(Protocol):
    name: str

    def status(self) -> ProviderStatus:
        """Return provider connection status for diagnostics."""

    def validate_symbol(self, symbol: str) -> str:
        """Normalize and validate a provider-supported symbol."""

    def validate_timeframe(self, timeframe: str) -> str:
        """Normalize and validate a provider-supported timeframe."""

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> list[CandleResponse]:
        """Fetch candles from the provider."""
