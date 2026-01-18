from functools import lru_cache
from typing_extensions import Annotated
from fastapi import APIRouter, Depends

from ...core import config


@lru_cache
def get_settings():
    return config.settings


router = APIRouter(
    prefix="",
    tags=["home", "info"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to Rent This Boat API"}


@router.get("/info")
async def info(settings: Annotated[config.Settings, Depends(get_settings)]):
    """Get application configuration info."""
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email,
        "items_per_user": settings.items_per_user,
        "mongo_uri": settings.mongo_uri,
    }
