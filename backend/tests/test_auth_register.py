"""Integration tests for POST /api/v1/auth/register.

MongoDB calls are patched so no real database is required.
The TestClient + lifespan mock is provided by the `client` conftest fixture.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

REGISTER_URL = "/api/v1/auth/register"

VALID_PAYLOAD = {
    "email": "jane.smith@example.com",
    "password": "SecurePass123!",
    "first_name": "Jane",
    "last_name": "Smith",
}


class TestRegisterSuccess:
    def test_returns_201_for_new_user(self, client):
        mock_instance = MagicMock()
        mock_instance.insert = AsyncMock()
        mock_instance.email = VALID_PAYLOAD["email"]
        mock_instance.first_name = VALID_PAYLOAD["first_name"]
        mock_instance.last_name = VALID_PAYLOAD["last_name"]

        with patch("app.api.v1.auth.User") as MockUser:
            MockUser.find_one = AsyncMock(return_value=None)
            MockUser.return_value = mock_instance

            response = client.post(REGISTER_URL, json=VALID_PAYLOAD)

        assert response.status_code == 201

    def test_response_body_contains_email_and_name(self, client):
        mock_instance = MagicMock()
        mock_instance.insert = AsyncMock()
        mock_instance.email = VALID_PAYLOAD["email"]
        mock_instance.first_name = VALID_PAYLOAD["first_name"]
        mock_instance.last_name = VALID_PAYLOAD["last_name"]

        with patch("app.api.v1.auth.User") as MockUser:
            MockUser.find_one = AsyncMock(return_value=None)
            MockUser.return_value = mock_instance

            response = client.post(REGISTER_URL, json=VALID_PAYLOAD)

        body = response.json()
        assert body["email"] == VALID_PAYLOAD["email"]
        assert body["first_name"] == VALID_PAYLOAD["first_name"]
        assert body["last_name"] == VALID_PAYLOAD["last_name"]


class TestRegisterConflict:
    def test_returns_409_for_duplicate_email(self, client):
        existing_user = MagicMock()

        with patch("app.api.v1.auth.User") as MockUser:
            MockUser.find_one = AsyncMock(return_value=existing_user)

            response = client.post(REGISTER_URL, json=VALID_PAYLOAD)

        assert response.status_code == 409

    def test_409_body_mentions_email(self, client):
        existing_user = MagicMock()

        with patch("app.api.v1.auth.User") as MockUser:
            MockUser.find_one = AsyncMock(return_value=existing_user)

            response = client.post(REGISTER_URL, json=VALID_PAYLOAD)

        detail = str(response.json())
        assert "email" in detail.lower()


class TestRegisterWeakPassword:
    @pytest.mark.parametrize(
        "bad_password",
        [
            "short",             # too short
            "nouppercase123!",   # missing uppercase
            "NOLOWERCASE123!",   # missing lowercase
            "NoDigitHereABC!!",  # missing digit
            "NoSpecialChar123",  # missing special char
        ],
    )
    def test_returns_400_for_weak_password(self, client, bad_password):
        payload = {**VALID_PAYLOAD, "password": bad_password}

        with patch("app.api.v1.auth.User") as MockUser:
            MockUser.find_one = AsyncMock(return_value=None)

            response = client.post(REGISTER_URL, json=payload)

        # 400 from PasswordValidator or 422 from Pydantic min_length
        assert response.status_code in (400, 422)


class TestRegisterValidation:
    def test_returns_422_for_invalid_email_format(self, client):
        payload = {**VALID_PAYLOAD, "email": "not-an-email"}
        response = client.post(REGISTER_URL, json=payload)
        assert response.status_code == 422

    def test_returns_422_when_email_missing(self, client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "email"}
        response = client.post(REGISTER_URL, json=payload)
        assert response.status_code == 422

    def test_returns_422_when_first_name_missing(self, client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "first_name"}
        response = client.post(REGISTER_URL, json=payload)
        assert response.status_code == 422

    def test_returns_422_when_last_name_missing(self, client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "last_name"}
        response = client.post(REGISTER_URL, json=payload)
        assert response.status_code == 422

    def test_returns_422_for_empty_body(self, client):
        response = client.post(REGISTER_URL, json={})
        assert response.status_code == 422


class TestRegisterDatabaseError:
    def test_returns_500_when_insert_raises(self, client):
        mock_instance = MagicMock()
        mock_instance.insert = AsyncMock(side_effect=Exception("DB unavailable"))
        mock_instance.email = VALID_PAYLOAD["email"]
        mock_instance.first_name = VALID_PAYLOAD["first_name"]
        mock_instance.last_name = VALID_PAYLOAD["last_name"]

        with patch("app.api.v1.auth.User") as MockUser:
            MockUser.find_one = AsyncMock(return_value=None)
            MockUser.return_value = mock_instance

            response = client.post(REGISTER_URL, json=VALID_PAYLOAD)

        assert response.status_code == 500
