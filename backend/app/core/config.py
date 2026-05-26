from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    # Application Settings
    app_name: str = "Rent This Boat API"
    admin_email: str = "admin@rentthisboat.com"
    items_per_user: int = 50
    app_env: str = "development"
    force_https: bool = False

    # MongoDB Configuration
    mongo_uri: str = "mongodb://localhost:27017/rentthisboat"
    mongo_db_username: str = "your_username"
    mongo_db_password: str = "your_password"

    # JWT Configuration
    jwt_secret_key: str = ""  # Must be loaded from .env
    jwt_issuer: str = "rent-this-boat-api"
    jwt_audience: str = "rent-this-boat-client"

    # Allowed JWT algorithms (not configurable via .env - security policy)
    jwt_allowed_algorithms: list[str] = ["HS256"]  # Only HS256 for single-service

    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
