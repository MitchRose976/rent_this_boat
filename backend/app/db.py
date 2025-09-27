from motor.motor_asyncio import AsyncIOMotorClient
import os
from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
mongodb_uri: str
db_name: str


class Config:
env_prefix = ''
env_file = '.env'


@lru_cache()
def get_settings() -> Settings:
return Settings(
mongodb_uri=os.environ.get('MONGODB_URI', ''),
db_name=os.environ.get('DB_NAME', 'boat_rental'),
)


settings = get_settings()
client = AsyncIOMotorClient(settings.mongodb_uri)
db = client[settings.db_name]