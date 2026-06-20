from datetime import datetime, timezone
from typing import Any

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover
    mt5 = None

from app.core.config import settings
from app.schemas.market import CandleResponse
from app.providers.base import ProviderStatus

SUPPORTED_SYMBOLS = {"XAUUSD", "EURUSD", "GBPUSD", "BTCUSD", "NQ"}
SUPPORTED_TIMEFRAMES = {"M1", "M5", "M15", "M30", "H1", "H4", "D1"}


class MT5ConnectionError(RuntimeError):
    pass


class MT5DataError(RuntimeError):
    pass


class MT5MarketDataProvider:
    name = "mt5"

    def status(self) -> ProviderStatus:
        if mt5 is None:
            return {
                "provider": self.name,
                "status": "package_not_installed",
                "message": "Install MetaTrader5 and run this service on the MT5 Windows host.",
            }

        initialized = self._initialize()
        if not initialized:
            code, message = mt5.last_error()
            return {
                "provider": self.name,
                "status": "not_connected",
                "error_code": str(code),
                "message": str(message),
            }

        account = mt5.account_info()
        terminal = mt5.terminal_info()
        if account is None:
            code, message = mt5.last_error()
            return {
                "provider": self.name,
                "status": "not_connected",
                "error_code": str(code),
                "message": str(message),
            }

        return {
            "provider": self.name,
            "status": "connected",
            "account": str(account.login),
            "server": str(account.server),
            "terminal_path": str(terminal.path) if terminal else "unknown",
        }

    def validate_symbol(self, symbol: str) -> str:
        normalized = symbol.upper()
        if normalized not in SUPPORTED_SYMBOLS:
            supported = ", ".join(sorted(SUPPORTED_SYMBOLS))
            raise ValueError(f"Unsupported MT5 symbol '{symbol}'. Supported symbols: {supported}")
        return normalized

    def validate_timeframe(self, timeframe: str) -> str:
        normalized = timeframe.upper()
        if normalized not in SUPPORTED_TIMEFRAMES:
            supported = ", ".join(sorted(SUPPORTED_TIMEFRAMES))
            raise ValueError(
                f"Unsupported MT5 timeframe '{timeframe}'. Supported timeframes: {supported}"
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
        if limit < 1 or limit > 5000:
            raise ValueError("MT5 candle limit must be between 1 and 5000.")

        self._ensure_initialized()
        if not mt5.symbol_select(normalized_symbol, True):
            code, message = mt5.last_error()
            raise MT5DataError(
                f"Symbol '{normalized_symbol}' is not available in MT5: {code} {message}"
            )

        rates = mt5.copy_rates_from_pos(
            normalized_symbol,
            self._timeframe_map()[normalized_timeframe],
            0,
            limit,
        )
        if rates is None:
            code, message = mt5.last_error()
            raise MT5DataError(f"Failed to fetch MT5 candles: {code} {message}")

        return [
            CandleResponse(
                time=datetime.fromtimestamp(int(rate["time"]), tz=timezone.utc),
                open=float(rate["open"]),
                high=float(rate["high"]),
                low=float(rate["low"]),
                close=float(rate["close"]),
                tick_volume=int(rate["tick_volume"]),
                spread=int(rate["spread"]),
            )
            for rate in rates
        ]

    def _ensure_initialized(self) -> None:
        if mt5 is None:
            raise MT5ConnectionError("MetaTrader5 package is not installed.")
        if not self._initialize():
            code, message = mt5.last_error()
            raise MT5ConnectionError(f"Failed to initialize MT5: {code} {message}")
        if self._should_explicit_login():
            authorized = mt5.login(
                login=settings.MT5_LOGIN,
                password=settings.MT5_PASSWORD,
                server=settings.MT5_SERVER,
                timeout=settings.MT5_TIMEOUT_MS,
            )
            if not authorized:
                code, message = mt5.last_error()
                raise MT5ConnectionError(f"Failed to authorize MT5: {code} {message}")

    def _initialize(self) -> bool:
        if mt5 is None:
            return False
        if settings.MT5_TERMINAL_PATH:
            return mt5.initialize(
                path=settings.MT5_TERMINAL_PATH,
                timeout=settings.MT5_TIMEOUT_MS,
            )
        return mt5.initialize(timeout=settings.MT5_TIMEOUT_MS)

    def _should_explicit_login(self) -> bool:
        return bool(
            settings.MT5_FORCE_LOGIN
            and settings.MT5_LOGIN
            and settings.MT5_PASSWORD
            and settings.MT5_SERVER
        )

    def _timeframe_map(self) -> dict[str, Any]:
        return {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
