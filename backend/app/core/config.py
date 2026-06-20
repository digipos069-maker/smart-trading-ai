from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Trading AI"
    API_V1_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/smart_trading_ai"
    )


settings = Settings()
