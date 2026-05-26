"""Tests for POST /api/v1/auth/login"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from tests.conftest import (
    TEST_CLIENT_ID,
    TEST_REDIRECT_URI,
    TEST_STATE,
    TEST_USER_ID,
    TEST_EMAIL,
)

LOGIN_URL = "/api/v1/auth/login"
TEST_PASSWORD = "Test@1234!"

# A minimal valid code_challenge — /login stores it verbatim, no verification here
TEST_CODE_CHALLENGE = "E9Mrozoa1W4oU3aTI-0yV8oF6aYTF3RjXVZ51t-XhcU"

# CSRF value used in both cookie and form field
CSRF_VALUE = "test-csrf-value-abcdefghijklmnop"


def make_valid_form(**overrides):
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "response_type": "code",
        "client_id": TEST_CLIENT_ID,
        "redirect_uri": TEST_REDIRECT_URI,
        "code_challenge": TEST_CODE_CHALLENGE,
        "code_challenge_method": "S256",
        "state": TEST_STATE,
        "scope": "boats:read",
        "csrf_token": CSRF_VALUE,
    }
    data.update(overrides)
    return data


def _make_active_user():
    user = MagicMock()
    user.id = TEST_USER_ID
    user.email = TEST_EMAIL
    user.is_active = True
    user.deleted_at = None
    user.password_hash = "hashed_password"
    user.save = AsyncMock()
    return user


class TestLoginCSRFProtection:
    def test_no_csrf_cookie_returns_403(self, client_no_auth, mock_oauth2_client):
        """When the CSRF cookie is absent the endpoint must reject the request."""
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            # Post form data with csrf_token field but NO cookie
            response = client_no_auth.post(LOGIN_URL, data=make_valid_form())

        assert response.status_code == 403
        assert "text/html" in response.headers["content-type"]

    def test_csrf_mismatch_returns_403(self, client_no_auth, mock_oauth2_client):
        """Cookie and form-field values must match (constant-time compare)."""
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(csrf_token="wrong-value-XXXXXXXXXXXXXXXX"),
                cookies={"csrf_token": CSRF_VALUE},
            )

        assert response.status_code == 403


class TestLoginClientValidation:
    def test_unknown_client_returns_400(self, client_no_auth):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=None)
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(),
                cookies={"csrf_token": CSRF_VALUE},
            )

        assert response.status_code == 400
        assert "text/html" in response.headers["content-type"]

    def test_inactive_client_returns_400(self, client_no_auth, mock_oauth2_client):
        mock_oauth2_client.is_active = False
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(),
                cookies={"csrf_token": CSRF_VALUE},
            )

        assert response.status_code == 400

    def test_invalid_redirect_uri_returns_400(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(redirect_uri="http://evil.example.com/cb"),
                cookies={"csrf_token": CSRF_VALUE},
            )

        assert response.status_code == 400


class TestLoginCredentials:
    def test_user_not_found_rerenders_form(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.User"
        ) as MockUser:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockUser.find_one = AsyncMock(return_value=None)
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(),
                cookies={"csrf_token": CSRF_VALUE},
            )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_wrong_password_rerenders_form(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.User"
        ) as MockUser, patch(
            "app.api.v1.auth.verify_password", return_value=False
        ):
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockUser.find_one = AsyncMock(return_value=_make_active_user())
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(),
                cookies={"csrf_token": CSRF_VALUE},
            )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_inactive_user_rerenders_form(self, client_no_auth, mock_oauth2_client):
        inactive_user = _make_active_user()
        inactive_user.is_active = False
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.User"
        ) as MockUser, patch(
            "app.api.v1.auth.verify_password", return_value=True
        ):
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockUser.find_one = AsyncMock(return_value=inactive_user)
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(),
                cookies={"csrf_token": CSRF_VALUE},
            )

        assert response.status_code == 200

    def test_deleted_user_rerenders_form(self, client_no_auth, mock_oauth2_client):
        deleted_user = _make_active_user()
        deleted_user.deleted_at = datetime.now(timezone.utc)
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.User"
        ) as MockUser, patch(
            "app.api.v1.auth.verify_password", return_value=True
        ):
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockUser.find_one = AsyncMock(return_value=deleted_user)
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(),
                cookies={"csrf_token": CSRF_VALUE},
            )

        assert response.status_code == 200


class TestLoginSuccess:
    def test_valid_login_returns_302_redirect(self, client_no_auth, mock_oauth2_client):
        mock_ac = MagicMock()
        mock_ac.insert = AsyncMock()
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.User"
        ) as MockUser, patch(
            "app.api.v1.auth.AuthorizationCode"
        ) as MockAC, patch(
            "app.api.v1.auth.verify_password", return_value=True
        ):
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockUser.find_one = AsyncMock(return_value=_make_active_user())
            MockAC.return_value = mock_ac
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(),
                cookies={"csrf_token": CSRF_VALUE},
                follow_redirects=False,
            )

        assert response.status_code == 302

    def test_redirect_location_contains_code(self, client_no_auth, mock_oauth2_client):
        mock_ac = MagicMock()
        mock_ac.insert = AsyncMock()
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.User"
        ) as MockUser, patch(
            "app.api.v1.auth.AuthorizationCode"
        ) as MockAC, patch(
            "app.api.v1.auth.verify_password", return_value=True
        ):
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockUser.find_one = AsyncMock(return_value=_make_active_user())
            MockAC.return_value = mock_ac
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(),
                cookies={"csrf_token": CSRF_VALUE},
                follow_redirects=False,
            )

        location = response.headers["location"]
        assert "code=" in location
        assert f"state={TEST_STATE}" in location

    def test_redirect_goes_to_registered_redirect_uri(
        self, client_no_auth, mock_oauth2_client
    ):
        mock_ac = MagicMock()
        mock_ac.insert = AsyncMock()
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.User"
        ) as MockUser, patch(
            "app.api.v1.auth.AuthorizationCode"
        ) as MockAC, patch(
            "app.api.v1.auth.verify_password", return_value=True
        ):
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockUser.find_one = AsyncMock(return_value=_make_active_user())
            MockAC.return_value = mock_ac
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(),
                cookies={"csrf_token": CSRF_VALUE},
                follow_redirects=False,
            )

        assert response.headers["location"].startswith(TEST_REDIRECT_URI)

    def test_csrf_cookie_cleared_on_success(self, client_no_auth, mock_oauth2_client):
        """After a successful login the CSRF cookie should be deleted."""
        mock_ac = MagicMock()
        mock_ac.insert = AsyncMock()
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.User"
        ) as MockUser, patch(
            "app.api.v1.auth.AuthorizationCode"
        ) as MockAC, patch(
            "app.api.v1.auth.verify_password", return_value=True
        ):
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockUser.find_one = AsyncMock(return_value=_make_active_user())
            MockAC.return_value = mock_ac
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(),
                cookies={"csrf_token": CSRF_VALUE},
                follow_redirects=False,
            )

        # FastAPI's delete_cookie sets Max-Age=0 — the cookie value will be empty
        # and the response will contain a set-cookie header for csrf_token
        set_cookie = response.headers.get("set-cookie", "")
        assert "csrf_token" in set_cookie

    def test_db_insert_failure_returns_500(self, client_no_auth, mock_oauth2_client):
        mock_ac = MagicMock()
        mock_ac.insert = AsyncMock(side_effect=Exception("DB write error"))
        with patch("app.api.v1.auth.OAuth2Client") as MockClient, patch(
            "app.api.v1.auth.User"
        ) as MockUser, patch(
            "app.api.v1.auth.AuthorizationCode"
        ) as MockAC, patch(
            "app.api.v1.auth.verify_password", return_value=True
        ):
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            MockUser.find_one = AsyncMock(return_value=_make_active_user())
            MockAC.return_value = mock_ac
            response = client_no_auth.post(
                LOGIN_URL,
                data=make_valid_form(),
                cookies={"csrf_token": CSRF_VALUE},
            )

        assert response.status_code == 500
        assert "text/html" in response.headers["content-type"]
