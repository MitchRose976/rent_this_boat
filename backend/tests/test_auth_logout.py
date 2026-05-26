"""Integration tests for POST /api/v1/auth/logout.

- `client`        fixture: get_current_user overridden → no real token needed.
- `client_no_auth` fixture: real dependency → no token → 401.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

LOGOUT_URL = "/api/v1/auth/logout"


class TestLogoutUnauthenticated:
    def test_returns_401_with_no_auth_header(self, client_no_auth):
        response = client_no_auth.post(LOGOUT_URL)
        assert response.status_code == 401

    def test_returns_401_with_malformed_bearer(self, client_no_auth):
        response = client_no_auth.post(
            LOGOUT_URL, headers={"Authorization": "NotBearer abc"}
        )
        assert response.status_code == 401

    def test_returns_401_with_garbage_token(self, client_no_auth):
        response = client_no_auth.post(
            LOGOUT_URL, headers={"Authorization": "Bearer not.a.real.token"}
        )
        assert response.status_code == 401


class TestLogoutAuthenticated:
    def test_returns_200_when_no_active_tokens(self, client):
        mock_query = MagicMock()
        mock_query.to_list = AsyncMock(return_value=[])

        with patch("app.api.v1.auth.RefreshToken") as MockRT:
            MockRT.find.return_value = mock_query
            response = client.post(
                LOGOUT_URL, headers={"Authorization": "Bearer ignored-by-override"}
            )

        assert response.status_code == 200

    def test_returns_200_and_revokes_active_tokens(self, client):
        mock_token = MagicMock()
        mock_token.save = AsyncMock()
        mock_query = MagicMock()
        mock_query.to_list = AsyncMock(return_value=[mock_token])

        with patch("app.api.v1.auth.RefreshToken") as MockRT:
            MockRT.find.return_value = mock_query
            response = client.post(
                LOGOUT_URL, headers={"Authorization": "Bearer ignored-by-override"}
            )

        assert response.status_code == 200
        assert mock_token.is_revoked is True
        mock_token.save.assert_awaited_once()

    def test_response_body_contains_message(self, client):
        mock_query = MagicMock()
        mock_query.to_list = AsyncMock(return_value=[])

        with patch("app.api.v1.auth.RefreshToken") as MockRT:
            MockRT.find.return_value = mock_query
            response = client.post(
                LOGOUT_URL, headers={"Authorization": "Bearer ignored-by-override"}
            )

        assert "message" in response.json()

    def test_response_has_cache_control_no_store(self, client):
        mock_query = MagicMock()
        mock_query.to_list = AsyncMock(return_value=[])

        with patch("app.api.v1.auth.RefreshToken") as MockRT:
            MockRT.find.return_value = mock_query
            response = client.post(
                LOGOUT_URL, headers={"Authorization": "Bearer ignored-by-override"}
            )

        assert response.headers.get("cache-control") == "no-store"

    def test_response_has_pragma_no_cache(self, client):
        mock_query = MagicMock()
        mock_query.to_list = AsyncMock(return_value=[])

        with patch("app.api.v1.auth.RefreshToken") as MockRT:
            MockRT.find.return_value = mock_query
            response = client.post(
                LOGOUT_URL, headers={"Authorization": "Bearer ignored-by-override"}
            )

        assert response.headers.get("pragma") == "no-cache"

    def test_revoked_count_in_response_message(self, client):
        tokens = [MagicMock() for _ in range(3)]
        for t in tokens:
            t.save = AsyncMock()

        mock_query = MagicMock()
        mock_query.to_list = AsyncMock(return_value=tokens)

        with patch("app.api.v1.auth.RefreshToken") as MockRT:
            MockRT.find.return_value = mock_query
            response = client.post(
                LOGOUT_URL, headers={"Authorization": "Bearer ignored-by-override"}
            )

        assert "3" in response.json()["message"]
