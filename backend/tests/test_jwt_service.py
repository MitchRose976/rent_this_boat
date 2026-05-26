"""Unit tests for JWTService — token creation, verification, and helpers."""

import pytest
import jwt as pyjwt
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.services.auth.jwt_service import JWTService

TEST_SECRET = "test-secret-key-for-unit-tests-minimum-32bytes!"
OTHER_SECRET = "other-secret-key-also-32-bytes-long-here!!"
USER_ID = "507f1f77bcf86cd799439011"
EMAIL = "test@example.com"
SCOPES = ["boats:read", "bookings:write"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_raw_token(overrides: dict) -> str:
    """Manually encode a JWT with arbitrary claims for edge-case tests."""
    base = {
        "sub": USER_ID,
        "email": EMAIL,
        "scopes": [],
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "jti": "test-jti",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "token_type": "access",
    }
    base.update(overrides)
    return pyjwt.encode(base, TEST_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# __init__ validation
# ---------------------------------------------------------------------------
class TestJWTServiceInit:
    def test_init_with_explicit_secret_key(self):
        svc = JWTService(secret_key=TEST_SECRET)
        assert svc.secret_key == TEST_SECRET

    def test_init_uses_settings_when_no_secret_provided(self):
        # JWT_SECRET_KEY env var is set in conftest, so settings.jwt_secret_key is non-empty
        svc = JWTService()
        assert len(svc.secret_key) >= 32

    def test_init_defaults_algorithm_to_hs256(self):
        svc = JWTService(secret_key=TEST_SECRET)
        assert svc.algorithm == "HS256"

    def test_init_raises_for_short_secret(self):
        with pytest.raises(ValueError, match="at least 32 bytes"):
            JWTService(secret_key="tooshort")

    def test_init_raises_for_empty_secret(self):
        with pytest.raises(ValueError):
            JWTService(secret_key="")

    def test_init_raises_for_disallowed_algorithm(self):
        with pytest.raises(ValueError, match="not allowed"):
            JWTService(secret_key=TEST_SECRET, algorithm="RS256")


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------
class TestCreateAccessToken:
    def setup_method(self):
        self.svc = JWTService(secret_key=TEST_SECRET)

    def test_returns_three_part_jwt_string(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, SCOPES)
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_claims_sub_email_scopes(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, SCOPES)
        payload = self.svc.verify_token(token)
        assert payload.sub == USER_ID
        assert payload.email == EMAIL
        assert payload.scopes == SCOPES

    def test_token_type_is_access(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, [])
        payload = self.svc.verify_token(token)
        assert payload.token_type == "access"

    def test_default_expiry_is_15_minutes(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, [])
        payload = self.svc.verify_token(token)
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(payload.exp, tz=timezone.utc)
        diff_seconds = (expires_at - now).total_seconds()
        assert 14 * 60 <= diff_seconds <= 15 * 60

    def test_custom_expiry_override(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, [], expires_in_minutes=60)
        payload = self.svc.verify_token(token)
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(payload.exp, tz=timezone.utc)
        diff_seconds = (expires_at - now).total_seconds()
        assert 59 * 60 <= diff_seconds <= 60 * 60

    def test_jti_is_unique_per_token(self):
        t1 = self.svc.create_access_token(USER_ID, EMAIL, [])
        t2 = self.svc.create_access_token(USER_ID, EMAIL, [])
        assert self.svc.verify_token(t1).jti != self.svc.verify_token(t2).jti

    def test_issuer_and_audience_from_settings(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, [])
        payload = self.svc.verify_token(token)
        assert payload.iss == settings.jwt_issuer
        assert payload.aud == settings.jwt_audience

    def test_empty_scopes_allowed(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, [])
        assert self.svc.verify_token(token).scopes == []


# ---------------------------------------------------------------------------
# create_refresh_token
# ---------------------------------------------------------------------------
class TestCreateRefreshToken:
    def setup_method(self):
        self.svc = JWTService(secret_key=TEST_SECRET)

    def test_returns_three_part_jwt_string(self):
        token = self.svc.create_refresh_token(USER_ID, EMAIL)
        assert len(token.split(".")) == 3

    def test_token_type_is_refresh(self):
        token = self.svc.create_refresh_token(USER_ID, EMAIL)
        payload = self.svc.verify_token(token)
        assert payload.token_type == "refresh"

    def test_scopes_are_always_empty(self):
        token = self.svc.create_refresh_token(USER_ID, EMAIL)
        assert self.svc.verify_token(token).scopes == []

    def test_sub_matches_user_id(self):
        token = self.svc.create_refresh_token(USER_ID, EMAIL)
        assert self.svc.verify_token(token).sub == USER_ID

    def test_default_expiry_is_1_day(self):
        token = self.svc.create_refresh_token(USER_ID, EMAIL)
        payload = self.svc.verify_token(token)
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(payload.exp, tz=timezone.utc)
        diff_hours = (expires_at - now).total_seconds() / 3600
        assert 23 <= diff_hours <= 24


# ---------------------------------------------------------------------------
# verify_token
# ---------------------------------------------------------------------------
class TestVerifyToken:
    def setup_method(self):
        self.svc = JWTService(secret_key=TEST_SECRET)

    def test_raises_expired_signature_error_for_expired_token(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, [], expires_in_minutes=-1)
        with pytest.raises(pyjwt.ExpiredSignatureError):
            self.svc.verify_token(token)

    def test_raises_invalid_token_error_for_tampered_signature(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, [])
        tampered = token[:-10] + "a" * 10
        with pytest.raises(pyjwt.InvalidTokenError):
            self.svc.verify_token(tampered)

    def test_raises_invalid_token_error_for_wrong_secret(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, [])
        other_svc = JWTService(secret_key=OTHER_SECRET)
        with pytest.raises(pyjwt.InvalidTokenError):
            other_svc.verify_token(token)

    def test_raises_for_token_type_neither_access_nor_refresh(self):
        token = _make_raw_token({"token_type": "magic"})
        with pytest.raises(pyjwt.InvalidTokenError):
            self.svc.verify_token(token)

    def test_raises_for_missing_sub_claim(self):
        token = _make_raw_token({"sub": None})
        with pytest.raises(pyjwt.InvalidTokenError):
            self.svc.verify_token(token)

    def test_raises_for_wrong_issuer(self):
        token = _make_raw_token({"iss": "evil-issuer"})
        with pytest.raises(pyjwt.InvalidTokenError):
            self.svc.verify_token(token)

    def test_raises_for_wrong_audience(self):
        token = _make_raw_token({"aud": "wrong-audience"})
        with pytest.raises(pyjwt.InvalidTokenError):
            self.svc.verify_token(token)

    def test_returns_payload_for_valid_access_token(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, SCOPES)
        payload = self.svc.verify_token(token)
        assert payload.sub == USER_ID
        assert payload.token_type == "access"

    def test_returns_payload_for_valid_refresh_token(self):
        token = self.svc.create_refresh_token(USER_ID, EMAIL)
        payload = self.svc.verify_token(token)
        assert payload.token_type == "refresh"


# ---------------------------------------------------------------------------
# Convenience methods
# ---------------------------------------------------------------------------
class TestConvenienceMethods:
    def setup_method(self):
        self.svc = JWTService(secret_key=TEST_SECRET)

    def test_get_user_id_from_token(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, [])
        assert self.svc.get_user_id_from_token(token) == USER_ID

    def test_get_scopes_from_token(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, SCOPES)
        assert self.svc.get_scopes_from_token(token) == SCOPES

    def test_is_token_expired_false_for_valid_token(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, [])
        assert self.svc.is_token_expired(token) is False

    def test_is_token_expired_true_for_expired_token(self):
        token = self.svc.create_access_token(USER_ID, EMAIL, [], expires_in_minutes=-1)
        assert self.svc.is_token_expired(token) is True

    def test_is_token_expired_false_for_garbage_input(self):
        # Invalid token should not raise — returns False
        assert self.svc.is_token_expired("not.a.token") is False
