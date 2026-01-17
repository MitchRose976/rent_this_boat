from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Rent This Boat API"
    admin_email: str = "admin@rentthisboat.com"
    items_per_user: int = 50
    mongo_uri: str = "mongodb://localhost:27017/rentthisboat"
    mongo_db_username: str = "your_username"
    mongo_db_password: str = "your_password"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env")
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
