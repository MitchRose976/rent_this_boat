from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .middleware import configure_middleware

from .db.init import init_db
from .api.v1.home import router as home_router
from .api.v1.auth import router as auth_router
from .core.limiter import limiter
from .services.auth.jwt_service import JWTService


# ============================================================================
# Application Lifespan Management
# ============================================================================
# Handles startup and shutdown events for the FastAPI application.
# On startup: initializes the MongoDB connection and verifies connectivity.
# On shutdown: gracefully closes the MongoDB connection.
# ============================================================================
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


# ============================================================================
# FastAPI Application Instance
# ============================================================================
# Creates the main FastAPI application with metadata and lifespan management.
# - title: API documentation title
# - description: API documentation description
# - version: semantic version of the API
# - lifespan: context manager for app startup/shutdown events
# ============================================================================
route_prefix = "/api/v1"
app = FastAPI(
    title="Rent This Boat API",
    description="OAuth2 + PKCE authentication with boat rental management",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=f"{route_prefix}/docs",
    redoc_url=f"{route_prefix}/redoc",
    openapi_url=f"{route_prefix}/openapi.json",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Middleware configuration
configure_middleware(app)

# Register routes
app.include_router(home_router, prefix=route_prefix)
app.include_router(auth_router, prefix=route_prefix)


def get_jwt_service() -> JWTService:
    return JWTService()


# Example usage in a route:
# @app.get("/some-protected-endpoint")
# async def protected(jwt_service: JWTService = Depends(get_jwt_service)):
#     ...
