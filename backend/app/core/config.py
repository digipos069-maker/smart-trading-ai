from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
    )

    PROJECT_NAME: str = "Smart Trading AI"
    API_V1_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    AUTO_CREATE_TABLES: bool = True
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/smart_trading_ai"
    )
    MT5_LOGIN: int | None = None
    MT5_PASSWORD: str | None = None
    MT5_SERVER: str | None = None
    MT5_TERMINAL_PATH: str | None = None
    MT5_FORCE_LOGIN: bool = False
    MT5_TIMEOUT_MS: int = 60_000


settings = Settings()
