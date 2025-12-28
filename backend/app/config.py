from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Rent This Boat API"
    admin_email: str = "admin@rentthisboat.com"
    items_per_user: int = 50
    mongo_uri: str = "mongodb://localhost:27017/rentthisboat"

    class Config:
        env_file = "../.env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
