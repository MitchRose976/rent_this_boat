from functools import lru_cache
from fastapi import Depends, FastAPI
from typing_extensions import Annotated

from .core import config
from .db.init import init_db
from .auth import router as auth_router


async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    client = None
    try:
        client = await init_db()
        await client.admin.command({"ping": 1})
        print("Pinged your deployment. You successfully connected to MongoDB!")
        print("Database initialized successfully. App started...")
        yield

    except Exception as e:
        print("Error during app startup: ", e)
        yield

    finally:
        print("App shutting down...")
        if client is not None:
            await client.close()
            print("App shut down successfully and MongoDB connection closed...")
        else:
            print("App shut down (no MongoDB connection to close)...")


app = FastAPI(
    title="Rent This Boat API",
    description="OAuth2 + PKCE authentication with boat rental management",
    version="0.1.0",
    lifespan=lifespan,
)


@lru_cache
def get_settings():
    return config.settings


# Include auth routes
app.include_router(auth_router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to Rent This Boat API"}


@app.get("/info")
async def info(settings: Annotated[config.Settings, Depends(get_settings)]):
    """Get application configuration info."""
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email,
        "items_per_user": settings.items_per_user,
        "mongo_uri": settings.mongo_uri,
    }
