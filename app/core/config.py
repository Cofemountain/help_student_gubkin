from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./oge_physics.db"
    BOT_TOKEN: Optional[str] = None
    MAX_BOT_TOKEN: Optional[str] = "f9LHodD0cOJQCqyrp7oKqKvmguaxmVwqIoT1TPaJhXIujDaMsz5BvR3_2Bp7bnqKw-6uOC7XpKRUb_1HyGkW"
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
