"""Centralized application settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEFAULT_PAGE_SIZE: int = 5
    MAX_PAGE_SIZE: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
