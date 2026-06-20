from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Market Data Proxy Service"
    ENVIRONMENT: str = "development"
    AUTO_CREATE_TABLES: bool = True
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/smart_trading_ai"
    )

    MARKET_DATA_PROVIDER: str = "mt5"
    MARKET_DATA_TIMEOUT_SECONDS: float = 15.0
    BINANCE_BASE_URL: str = "https://api.binance.com"
    OANDA_BASE_URL: str = "https://api-fxpractice.oanda.com"
    OANDA_API_TOKEN: str | None = None

    MT5_LOGIN: int | None = None
    MT5_PASSWORD: str | None = None
    MT5_SERVER: str | None = None
    MT5_TERMINAL_PATH: str | None = None
    MT5_FORCE_LOGIN: bool = False
    MT5_TIMEOUT_MS: int = 60_000

    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    TELEGRAM_NOTIFY_MARKET_ERRORS: bool = False


settings = Settings()
