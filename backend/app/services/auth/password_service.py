"""Password validation utilities for user registration and authentication."""

import re
from typing import Tuple


class PasswordValidator:
    """Validate password meets security requirements."""

    MIN_LENGTH = 12
    MAX_LENGTH = 128

    SPECIAL_CHARS = r"!@#$%^&*()_+-=\[\]{};:'\",.<>?/~`"

    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        """
        Validate password strength against security requirements.

        Requirements:
        - Minimum 12 characters
        - Maximum 128 characters
        - At least one uppercase letter (A-Z)
        - At least one lowercase letter (a-z)
        - At least one number (0-9)
        - At least one special character
        - No common patterns

        Args:
            password: The password to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if password meets all requirements
            - error_message: Empty string if valid, error description if invalid
        """

        # Check minimum length
        if len(password) < PasswordValidator.MIN_LENGTH:
            return (
                False,
                f"Password must be at least {PasswordValidator.MIN_LENGTH} characters",
            )

        # Check maximum length
        if len(password) > PasswordValidator.MAX_LENGTH:
            return (
                False,
                f"Password must not exceed {PasswordValidator.MAX_LENGTH} characters",
            )

        # Check for at least one uppercase letter
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter (A-Z)"

        # Check for at least one lowercase letter
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter (a-z)"

        # Check for at least one number
        if not re.search(r"\d", password):
            return False, "Password must contain at least one number (0-9)"

        # Check for at least one special character
        if not re.search(f"[{re.escape(PasswordValidator.SPECIAL_CHARS)}]", password):
            special_sample = (
                ", ".join(list(PasswordValidator.SPECIAL_CHARS[:8])) + ", etc."
            )
            return (
                False,
                f"Password must contain at least one special character ({special_sample})",
            )

        # Check against common patterns

        # Expanded set of common passwords (whole-password match only)
        common_passwords = {
            "password",
            "password1",
            "password123",
            "password1234",
            "qwerty",
            "qwerty123",
            "qwertyuiop",
            "letmein",
            "welcome",
            "admin",
            "administrator",
            "123456",
            "1234567",
            "12345678",
            "123456789",
            "1234567890",
            "000000",
            "111111",
            "123123",
            "abc123",
            "iloveyou",
            "trustno1",
            "changeme",
            "dragon",
            "master",
            "monkey",
            "shadow",
            "sunshine",
            "football",
            "baseball",
            "soccer",
            "test",
            "test123",
            "testtest",
            "passw0rd",
            "654321",
            "superman",
            "batman",
            "pokemon",
            "starwars",
            "letmein123",
            "welcome1",
            "welcome123",
            "admin123",
            "admin1",
            "root",
            "root123",
            "default",
            "default123",
            "guest",
            "guest123",
            "user",
            "user123",
            "mypassword",
            "yourpassword",
            "login",
            "login123",
            "access",
            "access123",
            "pw123456",
            "pw12345",
            "pw1234",
            "pw123",
            "pw1",
            "pw",
            "pwtest",
        }

        if password.lower() in common_passwords:
            return (
                False,
                "Please choose a stronger password",
            )

        return True, ""
