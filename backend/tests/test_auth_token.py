"""Tests for POST /api/v1/auth/token"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.auth.pkce import generate_code_challenge
from tests.conftest import (
    TEST_CLIENT_ID,
    TEST_REDIRECT_URI,
    TEST_USER_ID,
    TEST_EMAIL,
    TEST_SCOPES,
)

TOKEN_URL = "/api/v1/auth/token"

# A fixed, consistent verifier/challenge pair for PKCE tests
TEST_CODE_VERIFIER = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"  # 43 chars
TEST_CODE_CHALLENGE = generate_code_challenge(TEST_CODE_VERIFIER)
TEST_AUTH_CODE = "test-authorization-code-xxxxxxxxxxx"


def make_valid_form(**overrides):
    data = {
        "grant_type": "authorization_code",
        "client_id": TEST_CLIENT_ID,
        "code": TEST_AUTH_CODE,
        "code_verifier": TEST_CODE_VERIFIER,
        "redirect_uri": TEST_REDIRECT_URI,
    }
    data.update(overrides)
    return data


def make_mock_auth_code(
    used=False,
    expired=False,
    client_id=TEST_CLIENT_ID,
    redirect_uri=TEST_REDIRECT_URI,
    code_challenge=None,
):
    doc = MagicMock()
    doc.used = used
    doc.expires_at = (
        datetime(2000, 1, 1, tzinfo=timezone.utc)
        if expired
        else datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    doc.client_id = client_id
    doc.redirect_uri = redirect_uri
    doc.code_challenge_method = "S256"
    doc.code_challenge = code_challenge if code_challenge is not None else TEST_CODE_CHALLENGE
    doc.scopes = TEST_SCOPES
    doc.code = TEST_AUTH_CODE
    doc.user_id = TEST_USER_ID
    doc.save = AsyncMock()
    return doc


def make_mock_user(is_active=True):
    user = MagicMock()
    user.id = TEST_USER_ID
    user.email = TEST_EMAIL
    user.is_active = is_active
    user.deleted_at = None
    return user


class TestTokenGrantType:
    def test_wrong_grant_type_returns_400(self, client_no_auth):
        response = client_no_auth.post(
            TOKEN_URL, data=make_valid_form(grant_type="implicit")
        )
        assert response.status_code == 400

    def test_missing_grant_type_returns_422(self, client_no_auth):
        data = make_valid_form()
        data.pop("grant_type")
        response = client_no_auth.post(TOKEN_URL, data=data)
        assert response.status_code == 422


class TestTokenAuthCodeValidation:
    def test_unknown_code_returns_400(self, client_no_auth):
        with patch("app.api.v1.auth.AuthorizationCode") as MockAC:
            MockAC.find_one = AsyncMock(return_value=None)
            response = client_no_auth.post(TOKEN_URL, data=make_valid_form())

        assert response.status_code == 400

    def test_replayed_code_returns_400(self, client_no_auth):
        """Using an already-used code is a replay attack → 400."""
        mock_rt = MagicMock()
        mock_rt.is_revoked = False
        mock_rt.save = AsyncMock()
        mock_query = MagicMock()
        mock_query.to_list = AsyncMock(return_value=[mock_rt])

        with patch("app.api.v1.auth.AuthorizationCode") as MockAC, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockAC.find_one = AsyncMock(return_value=make_mock_auth_code(used=True))
            MockRT.find.return_value = mock_query
            response = client_no_auth.post(TOKEN_URL, data=make_valid_form())

        assert response.status_code == 400

    def test_replayed_code_revokes_existing_tokens(self, client_no_auth):
        """On replay attack, all tokens issued from that code must be revoked."""
        mock_rt = MagicMock()
        mock_rt.is_revoked = False
        mock_rt.save = AsyncMock()
        mock_query = MagicMock()
        mock_query.to_list = AsyncMock(return_value=[mock_rt])

        with patch("app.api.v1.auth.AuthorizationCode") as MockAC, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockAC.find_one = AsyncMock(return_value=make_mock_auth_code(used=True))
            MockRT.find.return_value = mock_query
            client_no_auth.post(TOKEN_URL, data=make_valid_form())

        assert mock_rt.is_revoked is True
        mock_rt.save.assert_called_once()

    def test_expired_code_returns_400(self, client_no_auth):
        with patch("app.api.v1.auth.AuthorizationCode") as MockAC:
            MockAC.find_one = AsyncMock(return_value=make_mock_auth_code(expired=True))
            response = client_no_auth.post(TOKEN_URL, data=make_valid_form())

        assert response.status_code == 400

    def test_client_id_mismatch_returns_400(self, client_no_auth):
        with patch("app.api.v1.auth.AuthorizationCode") as MockAC:
            MockAC.find_one = AsyncMock(
                return_value=make_mock_auth_code(client_id="different-client")
            )
            response = client_no_auth.post(TOKEN_URL, data=make_valid_form())

        assert response.status_code == 400

    def test_redirect_uri_mismatch_returns_400(self, client_no_auth):
        with patch("app.api.v1.auth.AuthorizationCode") as MockAC:
            MockAC.find_one = AsyncMock(
                return_value=make_mock_auth_code(redirect_uri="http://other.example.com/cb")
            )
            response = client_no_auth.post(TOKEN_URL, data=make_valid_form())

        assert response.status_code == 400


class TestTokenPKCEValidation:
    def test_wrong_verifier_returns_400(self, client_no_auth):
        """code_verifier that doesn't match the stored challenge → 400."""
        wrong_verifier = "a" * 43  # Valid length, but won't match TEST_CODE_CHALLENGE
        with patch("app.api.v1.auth.AuthorizationCode") as MockAC:
            MockAC.find_one = AsyncMock(return_value=make_mock_auth_code())
            response = client_no_auth.post(
                TOKEN_URL, data=make_valid_form(code_verifier=wrong_verifier)
            )

        assert response.status_code == 400


class TestTokenUserValidation:
    def test_user_not_found_returns_500(self, client_no_auth):
        with patch("app.api.v1.auth.AuthorizationCode") as MockAC, patch(
            "app.api.v1.auth.User"
        ) as MockUser:
            MockAC.find_one = AsyncMock(return_value=make_mock_auth_code())
            MockUser.get = AsyncMock(return_value=None)
            response = client_no_auth.post(TOKEN_URL, data=make_valid_form())

        assert response.status_code == 500

    def test_inactive_user_returns_400(self, client_no_auth):
        with patch("app.api.v1.auth.AuthorizationCode") as MockAC, patch(
            "app.api.v1.auth.User"
        ) as MockUser:
            MockAC.find_one = AsyncMock(return_value=make_mock_auth_code())
            MockUser.get = AsyncMock(return_value=make_mock_user(is_active=False))
            response = client_no_auth.post(TOKEN_URL, data=make_valid_form())

        assert response.status_code == 400


class TestTokenClientCheck:
    def test_inactive_client_at_exchange_returns_400(
        self, client_no_auth, mock_oauth2_client
    ):
        """Client may be deactivated between /authorize and /token calls."""
        mock_oauth2_client.is_active = False
        with patch("app.api.v1.auth.AuthorizationCode") as MockAC, patch(
            "app.api.v1.auth.User"
        ) as MockUser, patch(
            "app.api.v1.auth.OAuth2Client"
        ) as MockClient:
            MockAC.find_one = AsyncMock(return_value=make_mock_auth_code())
            MockUser.get = AsyncMock(return_value=make_mock_user())
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.post(TOKEN_URL, data=make_valid_form())

        assert response.status_code == 400


class TestTokenSuccess:
    def _do_valid_exchange(self, client_no_auth, mock_oauth2_client):
        mock_rt_instance = MagicMock()
        mock_rt_instance.insert = AsyncMock()
        with patch("app.api.v1.auth.AuthorizationCode") as MockAC, patch(
            "app.api.v1.auth.User"
        ) as MockUser, patch(
            "app.api.v1.auth.OAuth2Client"
        ) as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockAC.find_one = AsyncMock(return_value=make_mock_auth_code())
            MockUser.get = AsyncMock(return_value=make_mock_user())
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.return_value = mock_rt_instance
            response = client_no_auth.post(TOKEN_URL, data=make_valid_form())
        return response

    def test_valid_exchange_returns_200(self, client_no_auth, mock_oauth2_client):
        response = self._do_valid_exchange(client_no_auth, mock_oauth2_client)
        assert response.status_code == 200

    def test_response_contains_access_token(self, client_no_auth, mock_oauth2_client):
        response = self._do_valid_exchange(client_no_auth, mock_oauth2_client)
        data = response.json()
        assert "access_token" in data
        assert data["access_token"]  # non-empty string

    def test_response_contains_refresh_token(self, client_no_auth, mock_oauth2_client):
        response = self._do_valid_exchange(client_no_auth, mock_oauth2_client)
        data = response.json()
        assert "refresh_token" in data
        assert data["refresh_token"]  # non-empty string

    def test_response_token_type_is_bearer(self, client_no_auth, mock_oauth2_client):
        response = self._do_valid_exchange(client_no_auth, mock_oauth2_client)
        assert response.json()["token_type"] == "Bearer"

    def test_response_has_expires_in(self, client_no_auth, mock_oauth2_client):
        response = self._do_valid_exchange(client_no_auth, mock_oauth2_client)
        data = response.json()
        assert "expires_in" in data
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

    def test_response_has_cache_control_no_store(
        self, client_no_auth, mock_oauth2_client
    ):
        response = self._do_valid_exchange(client_no_auth, mock_oauth2_client)
        assert response.headers.get("cache-control") == "no-store"

    def test_auth_code_marked_used(self, client_no_auth, mock_oauth2_client):
        """The authorization code must be marked as used after a successful exchange."""
        mock_ac = make_mock_auth_code()
        mock_rt_instance = MagicMock()
        mock_rt_instance.insert = AsyncMock()
        with patch("app.api.v1.auth.AuthorizationCode") as MockAC, patch(
            "app.api.v1.auth.User"
        ) as MockUser, patch(
            "app.api.v1.auth.OAuth2Client"
        ) as MockClient, patch(
            "app.api.v1.auth.RefreshToken"
        ) as MockRT:
            MockAC.find_one = AsyncMock(return_value=mock_ac)
            MockUser.get = AsyncMock(return_value=make_mock_user())
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockRT.return_value = mock_rt_instance
            client_no_auth.post(TOKEN_URL, data=make_valid_form())

        assert mock_ac.used is True
        mock_ac.save.assert_called_once()
