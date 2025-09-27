from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Rent This Boat API"
    admin_email: str
    items_per_user: int = 50
    mongo_uri: str

    class Config:
        env_file = ".env"  # Path to your .env file
