from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Smart Trading AI"
    API_V1_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    AUTO_CREATE_TABLES: bool = True
    MARKET_DATA_PROVIDER: str = "mt5"
    MARKET_DATA_TIMEOUT_SECONDS: float = 15.0
    BINANCE_BASE_URL: str = "https://api.binance.com"
    OANDA_BASE_URL: str = "https://api-fxpractice.oanda.com"
    OANDA_API_TOKEN: str | None = None
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/smart_trading_ai"
    )
    MT5_LOGIN: int | None = None
    MT5_PASSWORD: str | None = None
    MT5_SERVER: str | None = None
    MT5_TERMINAL_PATH: str | None = None
    MT5_FORCE_LOGIN: bool = False
    MT5_TIMEOUT_MS: int = 60_000
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4.1-mini"
    OPENAI_TIMEOUT_SECONDS: float = 20.0
    MARKET_DATA_SERVICE_URL: str | None = "http://127.0.0.1:8010"
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    SIGNAL_ALERTS_ENABLED: bool = False
    SIGNAL_ALERT_SYMBOLS: str = "XAUUSD"
    SIGNAL_ALERT_TIMEFRAMES: str = "M5"
    SIGNAL_ALERT_INTERVAL_SECONDS: int = 300
    SIGNAL_ALERT_MIN_SCORE: int = 75
    SIGNAL_ALERT_CANDLE_LIMIT: int = 500
    SIGNAL_ALERT_SYNC_PROVIDER: str | None = None


settings = Settings()
