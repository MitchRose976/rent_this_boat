"""Tests for GET /api/v1/auth/authorize"""

import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import (
    TEST_CLIENT_ID,
    TEST_REDIRECT_URI,
    TEST_STATE,
)

AUTHORIZE_URL = "/api/v1/auth/authorize"

# A minimal valid code_challenge (43 chars of URL-safe base64 — not verified by /authorize)
TEST_CODE_CHALLENGE = "E9Mrozoa1W4oU3aTI-0yV8oF6aYTF3RjXVZ51t-XhcU"


def make_valid_params(**overrides):
    params = {
        "response_type": "code",
        "client_id": TEST_CLIENT_ID,
        "redirect_uri": TEST_REDIRECT_URI,
        "code_challenge": TEST_CODE_CHALLENGE,
        "code_challenge_method": "S256",
        "state": TEST_STATE,
        "scope": "boats:read",
    }
    params.update(overrides)
    return params


class TestAuthorizeValidRequest:
    def test_returns_200_html(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(AUTHORIZE_URL, params=make_valid_params())

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_sets_csrf_cookie(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(AUTHORIZE_URL, params=make_valid_params())

        assert "csrf_token" in response.cookies

    def test_csrf_cookie_is_httponly(self, client_no_auth, mock_oauth2_client):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(AUTHORIZE_URL, params=make_valid_params())

        set_cookie = response.headers.get("set-cookie", "")
        assert "httponly" in set_cookie.lower()

    def test_omitting_scope_uses_client_allowed_scopes(
        self, client_no_auth, mock_oauth2_client
    ):
        """When scope is omitted, the client's allowed_scopes are used — still 200."""
        params = make_valid_params()
        params.pop("scope")
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(AUTHORIZE_URL, params=params)

        assert response.status_code == 200


class TestAuthorizeClientValidation:
    def test_unknown_client_returns_400_html(self, client_no_auth):
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=None)
            response = client_no_auth.get(AUTHORIZE_URL, params=make_valid_params())

        assert response.status_code == 400
        assert "text/html" in response.headers["content-type"]

    def test_unknown_client_does_not_redirect(self, client_no_auth):
        """Must NOT redirect on client errors — redirect_uri may be untrustworthy."""
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=None)
            response = client_no_auth.get(
                AUTHORIZE_URL,
                params=make_valid_params(),
                follow_redirects=False,
            )

        assert response.status_code == 400

    def test_inactive_client_returns_400(self, client_no_auth, mock_oauth2_client):
        mock_oauth2_client.is_active = False
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(AUTHORIZE_URL, params=make_valid_params())

        assert response.status_code == 400
        assert "text/html" in response.headers["content-type"]


class TestAuthorizeRedirectUriValidation:
    def test_missing_redirect_uri_returns_400(self, client_no_auth, mock_oauth2_client):
        """Missing redirect_uri → 400 (must not redirect)."""
        params = make_valid_params()
        params.pop("redirect_uri")
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(
                AUTHORIZE_URL, params=params, follow_redirects=False
            )

        assert response.status_code == 400
        assert "text/html" in response.headers["content-type"]

    def test_unregistered_redirect_uri_returns_400(
        self, client_no_auth, mock_oauth2_client
    ):
        """Unregistered redirect_uri → 400 (must not redirect)."""
        params = make_valid_params(redirect_uri="http://evil.example.com/callback")
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(
                AUTHORIZE_URL, params=params, follow_redirects=False
            )

        assert response.status_code == 400


class TestAuthorizeResponseTypeValidation:
    def test_wrong_response_type_redirects_with_error(
        self, client_no_auth, mock_oauth2_client
    ):
        params = make_valid_params(response_type="token")
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(
                AUTHORIZE_URL, params=params, follow_redirects=False
            )

        assert response.status_code == 302
        assert "error=unsupported_response_type" in response.headers["location"]

    def test_wrong_response_type_redirect_includes_state(
        self, client_no_auth, mock_oauth2_client
    ):
        params = make_valid_params(response_type="token")
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(
                AUTHORIZE_URL, params=params, follow_redirects=False
            )

        assert f"state={TEST_STATE}" in response.headers["location"]

    def test_wrong_response_type_redirects_to_registered_uri(
        self, client_no_auth, mock_oauth2_client
    ):
        params = make_valid_params(response_type="token")
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(
                AUTHORIZE_URL, params=params, follow_redirects=False
            )

        assert response.headers["location"].startswith(TEST_REDIRECT_URI)


class TestAuthorizePKCEValidation:
    def test_plain_challenge_method_redirects_with_error(
        self, client_no_auth, mock_oauth2_client
    ):
        params = make_valid_params(code_challenge_method="plain")
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(
                AUTHORIZE_URL, params=params, follow_redirects=False
            )

        assert response.status_code == 302
        assert "error=" in response.headers["location"]

    def test_unknown_challenge_method_redirects_with_error(
        self, client_no_auth, mock_oauth2_client
    ):
        params = make_valid_params(code_challenge_method="RS256")
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(
                AUTHORIZE_URL, params=params, follow_redirects=False
            )

        assert response.status_code == 302


class TestAuthorizeScopeValidation:
    def test_invalid_scope_redirects_with_error(
        self, client_no_auth, mock_oauth2_client
    ):
        params = make_valid_params(scope="invalid:scope")
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(
                AUTHORIZE_URL, params=params, follow_redirects=False
            )

        assert response.status_code == 302
        assert "error=invalid_scope" in response.headers["location"]

    def test_partially_invalid_scopes_redirects_with_error(
        self, client_no_auth, mock_oauth2_client
    ):
        params = make_valid_params(scope="boats:read admin:delete")
        with patch("app.api.v1.auth.OAuth2Client") as MockClient:
            MockClient.find_one = AsyncMock(return_value=mock_oauth2_client)
            response = client_no_auth.get(
                AUTHORIZE_URL, params=params, follow_redirects=False
            )

        assert response.status_code == 302
        assert "error=invalid_scope" in response.headers["location"]
