from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Trading AI"
    API_V1_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"


settings = Settings()
