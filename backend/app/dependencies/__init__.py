"""FastAPI dependency injection utilities for authentication and authorization."""

from .auth import get_current_user

__all__ = ["get_current_user"]
