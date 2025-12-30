from fastapi import Depends, FastAPI
from typing_extensions import Annotated

from . import config
from .db import init_db
from .auth import router as auth_router


async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    await init_db()
    yield


app = FastAPI(
    title="Rent This Boat API",
    description="OAuth2 + PKCE authentication with boat rental management",
    version="0.1.0",
    lifespan=lifespan,
)

# Include auth routes
app.include_router(auth_router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to Rent This Boat API"}


@app.get("/info")
async def info(settings: Annotated[config.Settings, Depends(config.get_settings)]):
    """Get application configuration info."""
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email,
        "items_per_user": settings.items_per_user,
        "mongo_uri": settings.mongo_uri,
    }
