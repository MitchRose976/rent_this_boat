"""Tests for POST /api/v1/auth/revoke"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import TEST_CLIENT_ID

REVOKE_URL = "/api/v1/auth/revoke"
TEST_REFRESH_TOKEN = "test-refresh-token-value-for-revoke"


def make_form(**overrides):
    data = {
        "client_id": TEST_CLIENT_ID,
        "refresh_token": TEST_REFRESH_TOKEN,
    }
    data.update(overrides)
    return data


class TestRevokeAlwaysReturns200:
    def test_invalid_client_still_returns_200(self, client_no_auth):
        """RFC 7009 §2.2: the server must return 200 even for an invalid client."""
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=None)
            response = client_no_auth.post(REVOKE_URL, data=make_form())

        assert response.status_code == 200

    def test_inactive_client_still_returns_200(self, client_no_auth, mock_oauth2_client):
        mock_oauth2_client.is_active = False
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.post(REVOKE_URL, data=make_form())

        assert response.status_code == 200

    def test_unknown_token_returns_200(self, client_no_auth, mock_oauth2_client):
        """Attempting to revoke an unknown token must still return 200."""
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=None)
            response = client_no_auth.post(REVOKE_URL, data=make_form())

        assert response.status_code == 200

    def test_already_revoked_token_returns_200(self, client_no_auth, mock_oauth2_client):
        revoked_rt = MagicMock()
        revoked_rt.is_revoked = True
        revoked_rt.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        revoked_rt.save = AsyncMock()
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=revoked_rt)
            response = client_no_auth.post(REVOKE_URL, data=make_form())

        assert response.status_code == 200


class TestRevokeTokenRevocation:
    def test_valid_active_token_gets_revoked(self, client_no_auth, mock_oauth2_client):
        mock_rt = MagicMock()
        mock_rt.is_revoked = False
        mock_rt.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        mock_rt.save = AsyncMock()
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=mock_rt)
            response = client_no_auth.post(REVOKE_URL, data=make_form())

        assert response.status_code == 200
        assert mock_rt.is_revoked is True
        mock_rt.save.assert_called_once()

    def test_revoked_token_has_revoked_at_timestamp(
        self, client_no_auth, mock_oauth2_client
    ):
        mock_rt = MagicMock()
        mock_rt.is_revoked = False
        mock_rt.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        mock_rt.save = AsyncMock()
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=mock_rt)
            client_no_auth.post(REVOKE_URL, data=make_form())

        assert mock_rt.revoked_at is not None

    def test_expired_token_is_not_saved(self, client_no_auth, mock_oauth2_client):
        """Expired tokens are already invalid — no need to write a revocation record."""
        mock_rt = MagicMock()
        mock_rt.is_revoked = False
        mock_rt.expires_at = datetime(2000, 1, 1, tzinfo=timezone.utc)  # in the past
        mock_rt.save = AsyncMock()
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=mock_rt)
            response = client_no_auth.post(REVOKE_URL, data=make_form())

        assert response.status_code == 200
        mock_rt.save.assert_not_called()

    def test_already_revoked_token_is_not_saved_again(
        self, client_no_auth, mock_oauth2_client
    ):
        mock_rt = MagicMock()
        mock_rt.is_revoked = True
        mock_rt.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        mock_rt.save = AsyncMock()
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=mock_rt)
            client_no_auth.post(REVOKE_URL, data=make_form())

        mock_rt.save.assert_not_called()


class TestRevokeCacheControl:
    def test_valid_request_has_cache_control_no_store(
        self, client_no_auth, mock_oauth2_client
    ):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=None)
            response = client_no_auth.post(REVOKE_URL, data=make_form())

        assert response.headers.get("cache-control") == "no-store"

    def test_invalid_client_response_has_cache_control(self, client_no_auth):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=None)
            response = client_no_auth.post(REVOKE_URL, data=make_form())

        assert response.headers.get("cache-control") == "no-store"


class TestRevokeResponseBody:
    def test_response_has_message_field(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.find_one = AsyncMock(return_value=None)
            response = client_no_auth.post(REVOKE_URL, data=make_form())

        assert "message" in response.json()

    def test_invalid_client_response_has_message_field(self, client_no_auth):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=None)
            response = client_no_auth.post(REVOKE_URL, data=make_form())

        assert "message" in response.json()
