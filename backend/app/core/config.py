from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: str | None = None
    mongo_db: str = "evently"
    ticketmaster_api_key: str | None = None
    gemini_api_key: str | None = None
    frontend_url: str = "http://localhost:5173"
    default_city: str = "New York"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
