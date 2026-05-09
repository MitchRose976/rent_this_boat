from functools import lru_cache
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi
from typing import Any, Dict
from pathlib import Path
from ..schemas import User
from ..schemas.auth import AuthorizationCode, RefreshToken, OAuth2Client
from ..core import config
from beanie import init_beanie


@lru_cache
def get_settings():
    return config.settings


settings = get_settings()

env_path = Path(__file__).parent.parent.parent / ".env"
MONGO_URI = settings.mongo_uri


async def init_db():
    client: AsyncMongoClient[Dict[str, Any]] = AsyncMongoClient(
        MONGO_URI,
        server_api=ServerApi("1", strict=False, deprecation_errors=True),
        compressors="zstd,snappy,zlib",
    )

    await init_beanie(
        database=client.db_name,
        document_models=[User, AuthorizationCode, RefreshToken, OAuth2Client],
    )
    return client
