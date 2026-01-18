"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from typing_extensions import Annotated


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
