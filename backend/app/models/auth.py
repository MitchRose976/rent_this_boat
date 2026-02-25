"""Pydantic schemas and Beanie models for authentication endpoints."""

import datetime
from pydantic import BaseModel, EmailStr, Field
from beanie import Document, Indexed
from typing import List, Optional
from typing_extensions import Annotated


# ============================================================================
# User Registration Models
# ============================================================================
class RegisterRequest(BaseModel):
    """Schema for user registration request."""

    email: Annotated[
        EmailStr,
        Field(description="User email address"),
    ]
    password: Annotated[
        str,
        Field(
            min_length=12,
            max_length=128,
            description="Password (12-128 characters, must include uppercase, lowercase, number, and special character)",
        ),
    ]
    first_name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            description="User's first name",
        ),
    ]
    last_name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            description="User's last name",
        ),
    ]

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "john.doe@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
            }
        }
    }


class RegisterResponse(BaseModel):
    """Schema for successful registration response."""

    message: str
    user_id: str
    email: str
    first_name: str
    last_name: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Registration successful! You can now login.",
                "user_id": "507f1f77bcf86cd799439011",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
            }
        }
    }


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str
    detail: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Email already registered",
                "detail": "An account with this email already exists",
            }
        }
    }


# ============================================================================
# JWT Token Payload Model
# ============================================================================
class JwtTokenPayload(BaseModel):
    """
    JWT token claims following RFC 7519 standard.

    Registered Claims (RFC 7519):
    - sub: Subject (principal the JWT is about) - should be user_id
    - iss: Issuer (who created the JWT)
    - aud: Audience (who the JWT is intended for)
    - exp: Expiration time (Unix timestamp)
    - iat: Issued at time (Unix timestamp)
    - jti: JWT ID (unique identifier for this token)

    Private Claims (application-specific):
    - email: User's email address
    - scopes: List of permission scopes
    - token_type: "access" or "refresh"
    """

    # Registered Claims
    sub: str = Field(
        description="Subject - the user ID (MongoDB ObjectId as string)"
    )  # Required by OAuth2
    iss: str = Field(
        default="rent-this-boat-api",
        description="Issuer - who created the token",
    )
    aud: str = Field(
        default="rent-this-boat-client",
        description="Audience - who this token is intended for",
    )
    exp: int = Field(
        description="Expiration time (Unix timestamp)"
    )  # Unix timestamp, not datetime
    iat: int = Field(
        description="Issued at time (Unix timestamp)"
    )  # Unix timestamp, not datetime
    jti: str = Field(
        description="JWT ID - unique identifier for token revocation/tracking"
    )

    # Private Claims
    email: str = Field(description="User's email address")
    scopes: List[str] = Field(
        default_factory=list,
        description="Permission scopes (e.g., ['boats:read', 'bookings:write'])",
    )
    token_type: str = Field(
        description="Token type: 'access' (1 hour) or 'refresh' (7 days)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "sub": "507f1f77bcf86cd799439011",
                "iss": "rent-this-boat-api",
                "aud": "rent-this-boat-client",
                "exp": 1705953600,
                "iat": 1705950000,
                "jti": "abc123def456",
                "email": "user@example.com",
                "scopes": ["boats:read", "bookings:write"],
                "token_type": "access",
            }
        }
    }


# ============================================================================
# OAuth2 PKCE Models (Beanie Documents for MongoDB persistence)
# ============================================================================
class AuthorizationCode(Document):
    """
    Temporary authorization code issued during OAuth2 PKCE flow.

    Lifecycle:
    1. User initiates login, client generates PKCE code_verifier
    2. Client requests authorization code with code_challenge
    3. Server creates this record and returns code to client
    4. Client exchanges code + code_verifier for tokens
    5. Record is deleted/invalidated after exchange or expiration

    TTL: 5-10 minutes (expires automatically via MongoDB TTL index)

    Security:
    - code_challenge is derived from code_verifier (one-way hash)
    - Attacker with intercepted code cannot forge valid code_verifier
    - State prevents CSRF attacks (client must return same state)
    """

    user_id: Annotated[
        str,
        Field(description="MongoDB ObjectId of user who authorized (as string)"),
        Indexed(),
    ]
    code: Annotated[
        str,
        Field(
            min_length=32,
            max_length=128,
            description="Authorization code (random, high entropy)",
        ),
        Indexed(unique=True),
    ]
    code_challenge: Annotated[
        str,
        Field(
            description="PKCE code challenge (SHA256(verifier) base64url-encoded, 43 chars)",
        ),
    ]
    code_challenge_method: Annotated[
        str,
        Field(default="S256", description="PKCE method: S256 (SHA256) or plain"),
    ]
    state: Annotated[
        str,
        Field(
            min_length=32,
            max_length=128,
            description="State parameter (prevents CSRF, client must echo back)",
        ),
    ]
    client_id: Annotated[
        str,
        Field(description="OAuth2 client ID"),
        Indexed(),
    ]
    redirect_uri: Annotated[
        str,
        Field(
            description="Redirect URI this code is valid for (prevents redirect attacks)"
        ),
    ]
    scopes: Annotated[
        List[str],
        Field(default_factory=list, description="Scopes user authorized"),
    ]
    created_at: Annotated[
        datetime.datetime,
        Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)),
    ]
    expires_at: Annotated[
        datetime.datetime,
        Field(
            description="Expiration time (5-10 minutes after creation)",
            index={"expireAfterSeconds": 0},  # TTL index - auto-delete when expired
        ),
    ]

    class Settings:
        collection = "authorization_codes"

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "code": "auth_code_abc123xyz789...32chars_minimum",
                "code_challenge": "E9Mrozoa1W4oU3aTI-0yV8oF6aYTF3RjXVZ51t-XhcU",
                "code_challenge_method": "S256",
                "state": "state_parameter_xyz789...32chars_minimum",
                "client_id": "web-app-frontend",
                "redirect_uri": "https://localhost:3000/auth/callback",
                "scopes": ["boats:read", "bookings:write"],
                "created_at": "2026-01-24T10:00:00Z",
                "expires_at": "2026-01-24T10:05:00Z",
            }
        }
    }


class RefreshToken(Document):
    """
    Issued refresh token with revocation support.

    Lifecycle:
    1. During token exchange, server issues refresh token
    2. Server stores token_hash (never stores plaintext tokens)
    3. Client uses refresh token to request new access token
    4. Server validates token_hash and checks is_revoked flag
    5. Optional: admin can revoke all user's refresh tokens on logout

    TTL: 7 days (expires automatically via MongoDB TTL index)

    Security:
    - Only token_hash is stored (plaintext never in database)
    - is_revoked flag allows immediate revocation without database scan
    - Indexed by user_id for fast revocation of all tokens
    - Tokens automatically deleted after 7 days
    """

    user_id: Annotated[
        str,
        Field(description="MongoDB ObjectId of token owner (as string)"),
        Indexed(),
    ]
    token_hash: Annotated[
        str,
        Field(
            description="SHA256 hash of refresh token (plaintext never stored)",
        ),
        Indexed(unique=True),
    ]
    is_revoked: Annotated[
        bool,
        Field(
            default=False,
            description="True if token has been revoked (logout, compromised, etc)",
        ),
        Indexed(),
    ]
    revoked_at: Annotated[
        Optional[datetime.datetime],
        Field(
            default=None,
            description="Timestamp when token was revoked (null if not revoked)",
        ),
    ]
    issued_at: Annotated[
        datetime.datetime,
        Field(
            default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
            description="When refresh token was issued",
        ),
    ]
    expires_at: Annotated[
        datetime.datetime,
        Field(
            description="Expiration time (7 days after issued_at)",
            index={"expireAfterSeconds": 0},  # TTL index - auto-delete when expired
        ),
    ]
    device_info: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Optional device info (user agent, IP, etc for security audit)",
        ),
    ]

    class Settings:
        collection = "refresh_tokens"

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "token_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6...",
                "is_revoked": False,
                "revoked_at": None,
                "issued_at": "2026-01-24T10:00:00Z",
                "expires_at": "2026-01-31T10:00:00Z",
                "device_info": "Chrome 120 on Windows 10",
            }
        }
    }


class OAuth2Client(Document):
    """
    OAuth2 client application configuration.

    Stores client credentials and allowed redirect URIs.
    Used to validate client requests and prevent redirect attacks.

    Security:
    - client_secret is hashed (never stored plaintext)
    - redirect_uris must match exactly (prevents redirect attacks)
    - allowed_scopes limits what clients can request
    - is_active flag disables compromised clients
    """

    client_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=128,
            description="Unique client identifier (e.g., 'web-app-frontend')",
        ),
        Indexed(unique=True),
    ]
    client_secret_hash: Annotated[
        str,
        Field(
            description="Bcrypt hash of client secret (plaintext never stored)",
        ),
    ]
    client_name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=255,
            description="Human-readable client name",
        ),
    ]
    redirect_uris: Annotated[
        List[str],
        Field(
            min_length=1,
            description="Allowed redirect URIs (exact match required)",
        ),
    ]
    allowed_scopes: Annotated[
        List[str],
        Field(
            default_factory=lambda: ["boats:read"],
            description="Scopes this client is permitted to request",
        ),
    ]
    is_active: Annotated[
        bool,
        Field(
            default=True,
            description="If false, client is disabled (denied all requests)",
        ),
        Indexed(),
    ]
    owner_email: Annotated[
        str,
        Field(description="Email of person/team responsible for this client"),
    ]
    created_at: Annotated[
        datetime.datetime,
        Field(
            default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
    ]
    created_by: Annotated[
        str,
        Field(
            description="User ID of admin who created this client",
        ),
    ]

    class Settings:
        collection = "oauth2_clients"

    model_config = {
        "json_schema_extra": {
            "example": {
                "client_id": "web-app-frontend",
                "client_secret_hash": "$2b$12$OIX.NQPVJX2L.G...bcrypt_hash...",
                "client_name": "Rent This Boat Web App",
                "redirect_uris": [
                    "https://localhost:3000/auth/callback",
                    "https://app.rentthisboat.com/auth/callback",
                ],
                "allowed_scopes": [
                    "boats:read",
                    "boats:write",
                    "bookings:read",
                    "bookings:write",
                ],
                "is_active": True,
                "owner_email": "devops@rentthisboat.com",
                "created_at": "2026-01-24T10:00:00Z",
                "created_by": "507f1f77bcf86cd799439011",
            }
        }
    }
