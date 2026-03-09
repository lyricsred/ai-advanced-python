import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'URL Shortener API'
    debug: bool = False
    database_url: str = 'postgresql://user:password@localhost:5432/shortener'
    redis_url: str = 'redis://localhost:6379/0'
    cache_ttl_seconds: int = 3600
    secret_key: str = 'change-me-in-production'
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60 * 24
    short_code_length: int = 6

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
