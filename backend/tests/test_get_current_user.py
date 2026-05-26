"""Unit tests for the get_current_user FastAPI dependency.

These tests call the async dependency function directly (no TestClient needed)
and mock the DB lookup so no real MongoDB is required.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, Request

from app.dependencies.auth import get_current_user
from tests.conftest import TEST_JWT_SECRET, TEST_USER_ID, TEST_EMAIL, TEST_SCOPES
from app.services.auth.jwt_service import JWTService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_svc = JWTService(secret_key=TEST_JWT_SECRET)


def _make_request(authorization: str | None = None) -> Request:
    """Return a mock Request with the supplied Authorization header."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"Authorization": authorization} if authorization else {}
    return mock_req


def _valid_access_token() -> str:
    return _svc.create_access_token(TEST_USER_ID, TEST_EMAIL, TEST_SCOPES)


def _valid_refresh_token() -> str:
    return _svc.create_refresh_token(TEST_USER_ID, TEST_EMAIL)


def _expired_access_token() -> str:
    return _svc.create_access_token(TEST_USER_ID, TEST_EMAIL, [], expires_in_minutes=-1)


# ---------------------------------------------------------------------------
# Missing / malformed Authorization header
# ---------------------------------------------------------------------------
class TestMissingOrMalformedHeader:
    async def test_raises_401_when_header_absent(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(_make_request())
        assert exc_info.value.status_code == 401

    async def test_raises_401_when_scheme_is_not_bearer(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(_make_request("Basic dXNlcjpwYXNz"))
        assert exc_info.value.status_code == 401

    async def test_raises_401_when_only_bearer_keyword_present(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(_make_request("Bearer"))
        assert exc_info.value.status_code == 401

    async def test_raises_401_when_too_many_parts(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(_make_request("Bearer tok extra"))
        assert exc_info.value.status_code == 401

    async def test_www_authenticate_header_present_on_401(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(_make_request())
        assert "WWW-Authenticate" in exc_info.value.headers


# ---------------------------------------------------------------------------
# Invalid / expired tokens
# ---------------------------------------------------------------------------
class TestInvalidTokens:
    async def test_raises_401_for_expired_token(self):
        token = _expired_access_token()
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(_make_request(f"Bearer {token}"))
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    async def test_raises_401_for_garbage_token(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(_make_request("Bearer this.is.garbage"))
        assert exc_info.value.status_code == 401

    async def test_raises_401_when_refresh_token_used_as_access_token(self):
        token = _valid_refresh_token()
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(_make_request(f"Bearer {token}"))
        assert exc_info.value.status_code == 401
        assert "refresh" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# DB lookups — user state
# ---------------------------------------------------------------------------
class TestUserStateLookup:
    async def test_raises_401_when_user_not_found_in_db(self):
        token = _valid_access_token()
        with patch("app.db.models.user.User.get", new=AsyncMock(return_value=None)):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(_make_request(f"Bearer {token}"))
        assert exc_info.value.status_code == 401

    async def test_raises_403_when_user_is_inactive(self):
        token = _valid_access_token()
        inactive_user = MagicMock()
        inactive_user.is_active = False
        inactive_user.deleted_at = None
        with patch(
            "app.db.models.user.User.get", new=AsyncMock(return_value=inactive_user)
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(_make_request(f"Bearer {token}"))
        assert exc_info.value.status_code == 403

    async def test_raises_403_when_user_is_soft_deleted(self):
        token = _valid_access_token()
        deleted_user = MagicMock()
        deleted_user.is_active = True
        deleted_user.deleted_at = datetime.now(timezone.utc)
        with patch(
            "app.db.models.user.User.get", new=AsyncMock(return_value=deleted_user)
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(_make_request(f"Bearer {token}"))
        assert exc_info.value.status_code == 403

    async def test_raises_500_when_db_lookup_raises(self):
        token = _valid_access_token()
        with patch(
            "app.db.models.user.User.get",
            new=AsyncMock(side_effect=Exception("DB error")),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(_make_request(f"Bearer {token}"))
        assert exc_info.value.status_code == 500

    async def test_returns_user_for_valid_active_token(self):
        token = _valid_access_token()
        active_user = MagicMock()
        active_user.is_active = True
        active_user.deleted_at = None
        with patch(
            "app.db.models.user.User.get", new=AsyncMock(return_value=active_user)
        ):
            result = await get_current_user(_make_request(f"Bearer {token}"))
        assert result is active_user
