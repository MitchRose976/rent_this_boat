"""Tests for POST /api/v1/auth/refresh"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import (
    TEST_CLIENT_ID,
    TEST_USER_ID,
    TEST_EMAIL,
    TEST_SCOPES,
)

REFRESH_URL = "/api/v1/auth/refresh"
TEST_REFRESH_TOKEN = "test-refresh-token-value-abcdefghij"


def make_form(**overrides):
    data = {
        "client_id": TEST_CLIENT_ID,
        "refresh_token": TEST_REFRESH_TOKEN,
    }
    data.update(overrides)
    return data


def make_mock_refresh_token(is_revoked=False, expired=False):
    doc = MagicMock()
    doc.is_revoked = is_revoked
    doc.expires_at = (
        datetime(2000, 1, 1, tzinfo=timezone.utc)
        if expired
        else datetime.now(timezone.utc) + timedelta(days=1)
    )
    doc.user_id = TEST_USER_ID
    doc.scopes = TEST_SCOPES
    return doc


def make_mock_user(is_active=True, deleted=False):
    user = MagicMock()
    user.id = TEST_USER_ID
    user.email = TEST_EMAIL
    user.is_active = is_active
    user.deleted_at = datetime.now(timezone.utc) if deleted else None
    return user


class TestRefreshClientValidation:
    def test_unknown_client_returns_400(self, client_no_auth):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=None)
            response = client_no_auth.post(REFRESH_URL, data=make_form())

        assert response.status_code == 400

    def test_inactive_client_returns_400(self, client_no_auth, mock_oauth2_client):
        mock_oauth2_client.is_active = False
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.post(REFRESH_URL, data=make_form())

        assert response.status_code == 400


class TestRefreshTokenValidation:
    def test_unknown_token_returns_400(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=None)
            response = client_no_auth.post(REFRESH_URL, data=make_form())

        assert response.status_code == 400

    def test_revoked_token_returns_400(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(
                return_value=make_mock_refresh_token(is_revoked=True)
            )
            response = client_no_auth.post(REFRESH_URL, data=make_form())

        assert response.status_code == 400

    def test_expired_token_returns_400(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(
                return_value=make_mock_refresh_token(expired=True)
            )
            response = client_no_auth.post(REFRESH_URL, data=make_form())

        assert response.status_code == 400


class TestRefreshUserValidation:
    def test_user_not_found_returns_400(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT, patch("app.api.v1.auth.User") as MockUser:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=make_mock_refresh_token())
            MockUser.get = AsyncMock(return_value=None)
            response = client_no_auth.post(REFRESH_URL, data=make_form())

        assert response.status_code == 400

    def test_inactive_user_returns_400(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT, patch("app.api.v1.auth.User") as MockUser:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=make_mock_refresh_token())
            MockUser.get = AsyncMock(return_value=make_mock_user(is_active=False))
            response = client_no_auth.post(REFRESH_URL, data=make_form())

        assert response.status_code == 400

    def test_deleted_user_returns_400(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT, patch("app.api.v1.auth.User") as MockUser:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=make_mock_refresh_token())
            MockUser.get = AsyncMock(return_value=make_mock_user(deleted=True))
            response = client_no_auth.post(REFRESH_URL, data=make_form())

        assert response.status_code == 400


class TestRefreshSuccess:
    def _do_valid_refresh(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT, patch("app.api.v1.auth.User") as MockUser:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=make_mock_refresh_token())
            MockUser.get = AsyncMock(return_value=make_mock_user())
            response = client_no_auth.post(REFRESH_URL, data=make_form())
        return response

    def test_valid_refresh_returns_200(self, client_no_auth, mock_oauth2_client):
        response = self._do_valid_refresh(client_no_auth, mock_oauth2_client)
        assert response.status_code == 200

    def test_response_contains_access_token(self, client_no_auth, mock_oauth2_client):
        response = self._do_valid_refresh(client_no_auth, mock_oauth2_client)
        data = response.json()
        assert "access_token" in data
        assert data["access_token"]

    def test_response_does_not_contain_new_refresh_token(
        self, client_no_auth, mock_oauth2_client
    ):
        """The /refresh endpoint issues only an access token, not a new refresh token."""
        response = self._do_valid_refresh(client_no_auth, mock_oauth2_client)
        data = response.json()
        assert data.get("refresh_token") is None

    def test_response_has_cache_control_no_store(
        self, client_no_auth, mock_oauth2_client
    ):
        response = self._do_valid_refresh(client_no_auth, mock_oauth2_client)
        assert response.headers.get("cache-control") == "no-store"

    def test_response_has_expires_in(self, client_no_auth, mock_oauth2_client):
        response = self._do_valid_refresh(client_no_auth, mock_oauth2_client)
        data = response.json()
        assert "expires_in" in data
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0
