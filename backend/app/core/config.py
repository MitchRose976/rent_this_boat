from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).parent.parent.parent / ".env"
print(f"[DEBUG] Looking for .env at: {env_path}")
print(f"[DEBUG] .env exists: {env_path.exists()}")


class Settings(BaseSettings):
    app_name: str = "Rent This Boat API"
    admin_email: str = "admin@rentthisboat.com"
    items_per_user: int = 50
    mongo_uri: str = "mongodb://localhost:27017/rentthisboat"
    mongo_db_username: str = "your_username"
    mongo_db_password: str = "your_password"

    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
