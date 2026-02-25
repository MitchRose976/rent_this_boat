"""JWT (JSON Web Token) utilities for OAuth2 access tokens.

JWTs are self-contained tokens that allow stateless authentication.
Instead of storing session data on server, the token contains the data (claims)
and is cryptographically signed so the server can trust it hasn't been tampered with.

JWT Structure: header.payload.signature
- header: algorithm (HS256, RS256, etc.) and token type
- payload: claims (user_id, scopes, expiration, etc.)
- signature: HMAC-SHA256(header.payload, secret_key)

Flow:
1. Server creates JWT with user_id + scopes
2. Server signs it with secret key
3. Client stores JWT and sends it with each API request
4. Server verifies signature (proves token wasn't modified)
5. Server reads claims (user_id, scopes) from payload
6. Server checks expiration (token not stale)
"""

import jwt
import secrets
import base64
from datetime import datetime, timedelta, timezone
from typing import List
from app.core.config import settings
from app.models.auth import JwtTokenPayload


class JWTService:
    """Service for creating and validating JWT tokens."""

    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = None,
        access_token_expire_minutes: int = None,
        refresh_token_expire_days: int = None,
    ):
        """
        Initialize JWT service.

        Args:
            secret_key: Secret key for signing tokens (should be 32+ chars).
                       If None, loads from settings.jwt_secret_key
            algorithm: JWT algorithm (HS256 = HMAC-SHA256).
                      If None, loads from settings.jwt_algorithm
            access_token_expire_minutes: Expiration time for access tokens.
                                        If None, loads from settings
            refresh_token_expire_days: Expiration time for refresh tokens.
                                      If None, loads from settings

        Raises:
            ValueError: If secret_key is not provided or is too weak

        Note:
            For production, use RS256 (RSA) with public/private keys if you need
            token verification across multiple services.
        """
        self.secret_key = secret_key or settings.jwt_secret_key
        self.algorithm = algorithm or settings.jwt_algorithm # TODO: move algorithm out of .env since security decisions should be in code, not config
        self.access_token_expire_minutes = (
            access_token_expire_minutes or settings.jwt_access_token_expire_minutes
        )
        self.refresh_token_expire_days = (
            refresh_token_expire_days or settings.jwt_refresh_token_expire_days
        )

        # Validate secret key strength
        if not self.secret_key or len(self.secret_key.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET_KEY must be set and at least 32 bytes.")

        # Validate algorithm is whitelisted (prevents algorithm confusion attacks)
        if self.algorithm not in settings.JWT_ALLOWED_ALGORITHMS:
            raise ValueError(
                f"Algorithm '{self.algorithm}' not allowed. "
                f"Supported algorithms: {settings.JWT_ALLOWED_ALGORITHMS}."
            )

    @staticmethod
    def _generate_jti() -> str:
        """
        Generate a unique JWT ID (jti) using cryptographically secure randomness.

        Returns:
            URL-safe random string with ~256 bits of entropy.
        """
        return secrets.token_urlsafe(32)


    def create_access_token(
        self,
        user_id: str,
        email: str,
        scopes: List[str],
        expires_in_minutes: int = None,
    ) -> str:
        """
        Create a signed JWT access token.

        Args:
            user_id: User's MongoDB ObjectId (as string)
            email: User's email address
            scopes: List of permission scopes (e.g., ["boats:read", "bookings:write"])
            expires_in_minutes: Token expiration time. If None, uses default from settings (default 1 hour)

        Returns:
            Encoded JWT string (e.g., "eyJhbGc...")

        Example:
            >>> service = JWTService()  # Loads from settings
            >>> token = service.create_access_token(
            ...     user_id="507f1f77bcf86cd799439011",
            ...     email="user@example.com",
            ...     scopes=["boats:read", "bookings:write"],
            ... )
            >>> len(token) > 50
            True
        """
        if expires_in_minutes is None:
            expires_in_minutes = self.access_token_expire_minutes

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=expires_in_minutes)

        payload: JwtTokenPayload = {
            "sub": user_id,  # RFC 7519: subject (principal)
            "email": email,
            "scopes": scopes,
            "exp": int(expires_at.timestamp()),  # Unix timestamp
            "iat": int(now.timestamp()),  # Unix timestamp
            "jti": self._generate_jti(),  # Unique token ID for revocation tracking
            "iss": "rent-this-boat-api",
            "aud": "rent-this-boat-client",
            "token_type": "access",
        }

        # Encode the payload with secret key
        # jwt.encode() returns a string
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def create_refresh_token(
        self,
        user_id: str,
        email: str,
        expires_in_days: int = None,
    ) -> str:
        """
        Create a signed JWT refresh token.

        Refresh tokens live longer (days) than access tokens (hours).
        When access token expires, client uses refresh token to get a new one.

        Args:
            user_id: User's MongoDB ObjectId (as string)
            email: User's email address
            expires_in_days: Token expiration time. If None, uses default from settings (default 7 days)

        Returns:
            Encoded JWT string

        Example:
            >>> service = JWTService()  # Loads from settings
            >>> token = service.create_refresh_token(
            ...     user_id="507f1f77bcf86cd799439011",
            ...     email="user@example.com",
            ... )
        """
        if expires_in_days is None:
            expires_in_days = self.refresh_token_expire_days

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=expires_in_days)

        payload: JwtTokenPayload = {
            "sub": user_id,  # RFC 7519: subject (principal)
            "email": email,
            "scopes": [],  # refresh tokens don't have scopes
            "exp": int(expires_at.timestamp()),  # Unix timestamp
            "iat": int(now.timestamp()),  # Unix timestamp
            "jti": self._generate_jti(),  # Unique token ID for revocation tracking
            "iss": "rent-this-boat-api",
            "aud": "rent-this-boat-client",
            "token_type": "refresh",
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> JwtTokenPayload:
        """
        Verify and decode a JWT token with full validation.

        This function performs comprehensive JWT validation following RFC 7519 and
        OAuth2 best practices. It validates:
        - Signature (proves token wasn't tampered with) using HS256
        - Expiration (exp claim) - token not stale
        - Issuer (iss claim) - token came from expected service
        - Audience (aud claim) - token intended for this client
        - Algorithm (HS256 only, prevents algorithm confusion attacks)
        - Structure (Pydantic model validation of required claims)

        Security measures:
        - Whitelist algorithm approach (only HS256 allowed, prevents "none" algorithm)
        - Explicitly requires valid signature
        - Validates registered claims (iss, aud, exp, iat)
        - Rejects tokens with missing or invalid claims
        - Returns typed JwtTokenPayload for type safety

        Args:
            token: Encoded JWT string (format: header.payload.signature)

        Returns:
            JwtTokenPayload model with validated and typed claims

        Raises:
            jwt.ExpiredSignatureError: Token has expired (exp claim in past)
            jwt.InvalidTokenError:
                - Token signature is invalid or tampered with
                - Issuer (iss) doesn't match expected value
                - Audience (aud) doesn't match expected value
                - Algorithm is not HS256
                - Token is malformed or missing required claims
            ValueError: Token claims don't match JwtTokenPayload schema

        Example:
            >>> service = JWTService()  # Loads from settings
            >>> token = service.create_access_token("user123", "user@example.com", ["boats:read"])
            >>> claims = service.verify_token(token)
            >>> claims.sub
            'user123'
            >>> claims.scopes
            ['boats:read']
        """
        try:
            # Decode and verify the JWT with explicit security options
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],  # Whitelist: only HS256 allowed
                options={
                    "verify_signature": True,  # Require valid signature
                    "verify_exp": True,  # Verify expiration time
                },
                # Validate issuer (who created the token)
                issuer="rent-this-boat-api", # TODO: standardize issuer name
                # Validate audience (who the token is for)
                audience="rent-this-boat-client", # TODO: standardize audience name
            )

            # Validate payload structure and convert to typed model
            # Pydantic will raise ValueError if required fields are missing or invalid
            return JwtTokenPayload(**payload)

        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")
        except ValueError as e:
            # Pydantic validation failed (missing or invalid claims)
            raise jwt.InvalidTokenError(f"Invalid token claims: {str(e)}")

    def get_user_id_from_token(self, token: str) -> str:
        """
        Extract user_id from a valid token (convenience method).

        Args:
            token: Encoded JWT string

        Returns:
            User ID from token (extracted from 'sub' claim)

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        payload = self.verify_token(token)
        return payload.sub  # RFC 7519: subject claim contains user_id

    def get_scopes_from_token(self, token: str) -> List[str]:
        """
        Extract scopes from a valid token (convenience method).

        Args:
            token: Encoded JWT string

        Returns:
            List of scopes (permissions)

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        payload = self.verify_token(token)
        return payload.scopes

    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token is expired without raising exception.

        Args:
            token: Encoded JWT string

        Returns:
            True if token is expired, False if valid or error
        """
        try:
            self.verify_token(token)
            return False
        except jwt.ExpiredSignatureError:
            return True
        except jwt.InvalidTokenError:
            return False  # Invalid but not expired


# Example usage (for testing/learning):
if __name__ == "__main__":
    print("=== JWT Token Demonstration ===\n")

    # Initialize service with a secret key
    # In production, load this from environment variable
    service = JWTService(secret_key="your-super-secret-key-32-chars-minimum!!")

    print("1. Creating access token...")
    access_token = service.create_access_token(
        user_id="507f1f77bcf86cd799439011",
        email="jdoe@example.com",
        scopes=["boats:read", "bookings:write"],
        expires_in_minutes=60,
    )
    print(f"   Access Token: {access_token[:50]}...")
    print(f"   Length: {len(access_token)} characters\n")

    print("2. Creating refresh token...")
    refresh_token = service.create_refresh_token(
        user_id="507f1f77bcf86cd799439011",
        email="jdoe@example.com",
        expires_in_days=7,
    )
    print(f"   Refresh Token: {refresh_token[:50]}...")
    print(f"   Length: {len(refresh_token)} characters\n")

    print("3. Verifying access token...")
    payload = service.verify_token(access_token)
    print(f"   User ID: {payload.sub}")
    print(f"   Email: {payload.email}")
    print(f"   Scopes: {payload.scopes}")
    print(f"   Token Type: {payload.token_type}")
    print(f"   Token ID (jti): {payload.jti}")
    print(f"   Expires: {payload.exp}\n")

    print("4. Extracting specific claims...")
    user_id = service.get_user_id_from_token(access_token)
    scopes = service.get_scopes_from_token(access_token)
    print(f"   User ID: {user_id}")
    print(f"   Scopes: {scopes}\n")

    print("=== Attack Prevention ===\n")
    print("If attacker modifies token (e.g., changes 'a' to 'b')...")
    tampered_token = access_token[:-10] + "aaaaaaaaaa"  # Corrupt last 10 chars
    try:
        service.verify_token(tampered_token)
    except jwt.InvalidTokenError as e:
        print(f"   ✓ Caught tampering: {type(e).__name__}")

    print("\nIf attacker uses wrong secret key to verify...")
    wrong_service = JWTService(secret_key="different-secret-key-wrong!!")
    try:
        wrong_service.verify_token(access_token)
    except jwt.InvalidTokenError as e:
        print(f"   ✓ Caught wrong key: {type(e).__name__}")

    print("\n=== JWT Structure ===")
    print("JWT format: header.payload.signature")
    print(f"This token has 3 parts (separated by '.'):")
    parts = access_token.split(".")
    print(f"  1. Header (algorithm, token type): {parts[0][:30]}...")
    print(f"  2. Payload (claims): {parts[1][:50]}...")
    print(f"  3. Signature (HMAC): {parts[2][:30]}...")
