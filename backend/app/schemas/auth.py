from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from typing_extensions import Annotated
from ..constants import ACCESS_TOKEN_TTL, REFRESH_TOKEN_TTL


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
    email: str
    first_name: str
    last_name: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Registration successful! You can now login.",
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


class CurrentUserResponse(BaseModel):
    """Schema for current user information response."""

    id: str
    email: str
    first_name: str
    last_name: str
    role: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "customer",
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
        description=f"Token type: 'access' ({ACCESS_TOKEN_TTL['MINUTES']} minutes) or 'refresh' ({REFRESH_TOKEN_TTL['DAYS']} day(s))"
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


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str = Field(description="JWT access token")
    refresh_token: Optional[str] = Field(
        default=None,
        description="JWT refresh token (only returned on initial token exchange, not on refresh)",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (should be 'bearer')",
    )
    expires_in: int = Field(description="Access token expiration time in seconds")
    scope: Optional[str] = Field(
        default=None,
        description="Optional space-separated list of scopes granted by the token",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_TTL["SECONDS"],
                "scope": "boats:read bookings:write",
            }
        }
    }
