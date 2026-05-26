"""Authentication dependencies for FastAPI route protection.

This module provides injectable dependencies for protecting routes with JWT authentication.
Use these as FastAPI dependency injection to require authentication on protected endpoints.
"""

import jwt
from fastapi import status, HTTPException, Request
from app.services.auth.jwt_service import JWTService


async def get_current_user(request: Request):
    """
    FastAPI dependency to extract and validate the current user from Authorization header.

    Reads the JWT from the "Authorization: Bearer <token>" header, validates it,
    and returns the authenticated User object. Use as a dependency on protected routes.

    Args:
        request: FastAPI Request object containing headers

    Returns:
        User: The authenticated user document from database

    Raises:
        HTTPException 401: If Authorization header is missing or malformed
        HTTPException 401: If token is invalid, expired, or has wrong token_type
        HTTPException 403: If user is inactive or deleted
        HTTPException 500: If user lookup fails

    Example:
        @router.get("/me")
        async def get_profile(user: User = Depends(get_current_user)):
            return {"id": str(user.id), "email": user.email}
    """
    # Extract Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse "Bearer <token>" format
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Verify token and extract claims
    try:
        jwt_service = JWTService()
        payload = jwt_service.verify_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token is an access token (not a refresh token)
    if payload.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh tokens cannot be used to access protected resources",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Lookup user from database
    try:
        from app.db.models.user import User

        user = await User.get(payload.sub)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lookup user",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check user is active and not deleted
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted",
        )

    return user
