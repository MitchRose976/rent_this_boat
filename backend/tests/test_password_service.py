"""Unit tests for PasswordValidator — all validation rules."""

import pytest

from app.services.auth.password_service import PasswordValidator


class TestPasswordValidator:
    # ------------------------------------------------------------------
    # Valid passwords
    # ------------------------------------------------------------------
    def test_valid_password_passes(self):
        ok, msg = PasswordValidator.validate("SecurePass123!")
        assert ok is True
        assert msg == ""

    def test_valid_password_at_min_length(self):
        # Exactly 12 characters with all required character classes
        ok, msg = PasswordValidator.validate("SecureP1234!")
        assert ok is True

    def test_valid_password_at_max_length(self):
        # 128 characters: uppercase + lowercase + digit + special + padding
        password = "Aa1!" + "a" * 124
        assert len(password) == 128
        ok, msg = PasswordValidator.validate(password)
        assert ok is True

    # ------------------------------------------------------------------
    # Length violations
    # ------------------------------------------------------------------
    def test_rejects_password_shorter_than_minimum(self):
        ok, msg = PasswordValidator.validate("Short1!")
        assert ok is False
        assert str(PasswordValidator.MIN_LENGTH) in msg

    def test_rejects_password_longer_than_maximum(self):
        # 129 chars with all required classes
        password = "Aa1!" + "a" * 125
        assert len(password) == 129
        ok, msg = PasswordValidator.validate(password)
        assert ok is False
        assert str(PasswordValidator.MAX_LENGTH) in msg

    def test_empty_string_fails_length_check(self):
        ok, msg = PasswordValidator.validate("")
        assert ok is False

    # ------------------------------------------------------------------
    # Character class requirements
    # ------------------------------------------------------------------
    def test_rejects_missing_uppercase(self):
        ok, msg = PasswordValidator.validate("nouppercase123!")
        assert ok is False
        assert "uppercase" in msg.lower()

    def test_rejects_missing_lowercase(self):
        ok, msg = PasswordValidator.validate("NOLOWERCASE123!")
        assert ok is False
        assert "lowercase" in msg.lower()

    def test_rejects_missing_digit(self):
        ok, msg = PasswordValidator.validate("NoDigitHereABC!")
        assert ok is False
        assert "number" in msg.lower()

    def test_rejects_missing_special_character(self):
        ok, msg = PasswordValidator.validate("NoSpecialChar123")
        assert ok is False
        assert "special" in msg.lower()

    # ------------------------------------------------------------------
    # Each failing check returns a non-empty error message
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "password",
        [
            "short1A!",  # too short
            "nouppercase123!",  # no uppercase
            "NOLOWERCASE123!",  # no lowercase
            "NoDigitABCDEF!!",  # no digit
            "NoSpecialChar123",  # no special
        ],
    )
    def test_invalid_passwords_return_error_message(self, password):
        ok, msg = PasswordValidator.validate(password)
        assert ok is False
        assert len(msg) > 0
