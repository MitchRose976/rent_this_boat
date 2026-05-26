"""
Shared fixtures and configuration for the test suite.

Sets the JWT_SECRET_KEY environment variable BEFORE any app modules are
imported so that Pydantic Settings picks it up at instantiation time.
"""

import os

# Must be set before any app imports — Pydantic Settings reads env at class load.
TEST_JWT_SECRET = "test-secret-key-for-unit-tests-minimum-32bytes!"
os.environ.setdefault("JWT_SECRET_KEY", TEST_JWT_SECRET)

import pytest
from datetime import datetime, timezone
from app.core.limiter import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the in-memory rate limiter storage before every test to prevent 429s."""
    limiter._storage.reset()
    yield
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth import get_current_user
from app.services.auth.jwt_service import JWTService

# ---------------------------------------------------------------------------
# Constants shared across tests
# ---------------------------------------------------------------------------
TEST_USER_ID = "507f1f77bcf86cd799439011"
TEST_EMAIL = "testuser@example.com"
TEST_SCOPES = ["boats:read", "bookings:write"]

# OAuth2 / PKCE constants
TEST_CLIENT_ID = "test-client-id"
TEST_REDIRECT_URI = "http://localhost:3000/callback"
TEST_STATE = "a" * 32  # 32 chars, satisfies min_length=32


# ---------------------------------------------------------------------------
# Service fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def jwt_service():
    """JWTService initialised with the test secret key."""
    return JWTService(secret_key=TEST_JWT_SECRET)


@pytest.fixture
def access_token(jwt_service):
    """A fresh, valid access token for TEST_USER_ID."""
    return jwt_service.create_access_token(
        user_id=TEST_USER_ID,
        email=TEST_EMAIL,
        scopes=TEST_SCOPES,
    )


@pytest.fixture
def refresh_token(jwt_service):
    """A fresh, valid refresh token for TEST_USER_ID."""
    return jwt_service.create_refresh_token(
        user_id=TEST_USER_ID,
        email=TEST_EMAIL,
    )


@pytest.fixture
def expired_access_token(jwt_service):
    """An already-expired access token."""
    return jwt_service.create_access_token(
        user_id=TEST_USER_ID,
        email=TEST_EMAIL,
        scopes=[],
        expires_in_minutes=-1,
    )


# ---------------------------------------------------------------------------
# Mock user and OAuth2 client
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_user():
    """Mock User document returned by DB lookups in tests."""
    user = MagicMock()
    user.id = TEST_USER_ID
    user.email = TEST_EMAIL
    user.is_active = True
    user.deleted_at = None
    return user


@pytest.fixture
def mock_oauth2_client():
    """Mock OAuth2Client document for testing auth endpoints."""
    c = MagicMock()
    c.client_id = TEST_CLIENT_ID
    c.client_name = "Test App"
    c.is_active = True
    c.redirect_uris = [TEST_REDIRECT_URI]
    c.allowed_scopes = ["boats:read", "bookings:write"]
    return c


# ---------------------------------------------------------------------------
# HTTP test clients
# ---------------------------------------------------------------------------
@pytest.fixture
def client(mock_user):
    """
    TestClient with:
      - MongoDB init patched out (no real DB needed)
      - get_current_user dependency overridden to return mock_user

    Use this for testing authenticated endpoints without a real token.
    """
    mock_mongo = AsyncMock()
    mock_mongo.admin.command = AsyncMock()

    def override_auth():
        return mock_user

    app.dependency_overrides[get_current_user] = override_auth

    with patch("app.main.init_db", new=AsyncMock(return_value=mock_mongo)):
        with TestClient(app, base_url="http://testserver") as c:
            yield c

    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client_no_auth():
    """
    TestClient with MongoDB init patched out but NO dependency override.

    Use this to test that unauthenticated requests are properly rejected.
    """
    mock_mongo = AsyncMock()
    mock_mongo.admin.command = AsyncMock()

    with patch("app.main.init_db", new=AsyncMock(return_value=mock_mongo)):
        with TestClient(app, base_url="http://testserver") as c:
            yield c
