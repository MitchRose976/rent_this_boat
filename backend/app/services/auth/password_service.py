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
        common_patterns = [
            r"123",
            r"abc",
            r"qwerty",
            r"password",
            r"admin",
            r"letmein",
            r"welcome",
            r"12345",
            r"000000",
        ]

        for pattern in common_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                return (
                    False,
                    "Password contains common patterns (avoid: 123, abc, password, etc.)",
                )

        return True, ""
