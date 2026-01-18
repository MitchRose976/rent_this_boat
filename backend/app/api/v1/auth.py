"""Authentication endpoints for user registration, login, and token management."""

from fastapi import APIRouter, status, HTTPException
from datetime import datetime, timezone

from ...services.auth.utils import hash_password
from ...services.auth.password_service import PasswordValidator
from ...models.auth import ErrorResponse, RegisterRequest, RegisterResponse
from ...models.user import User

# Create router for auth endpoints
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password. Password must contain uppercase, lowercase, number, and special character.",
)
async def register(request: RegisterRequest) -> RegisterResponse:
    """
    Register a new user account.

    Validates:
    - Email format and uniqueness
    - Password strength requirements
    - User data completeness

    Args:
        request: RegisterRequest with email, password, first_name, last_name

    Returns:
        RegisterResponse with user details and success message

    Raises:
        HTTPException 400: Password validation failed
        HTTPException 409: Email already registered
        HTTPException 500: Database error
    """

    # Step 1: Validate password strength
    is_valid, error_message = PasswordValidator.validate(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    # Step 2: Check if email already exists (unique constraint)
    existing_user = await User.find_one(User.email == request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered. Please use a different email or try logging in.",
        )

    # Step 3: Hash password
    password_hash = hash_password(request.password)

    # Step 4: Create new user document
    new_user = User(
        email=request.email,
        password_hash=password_hash,
        first_name=request.first_name,
        last_name=request.last_name,
        is_active=True,
        is_verified=True,  # No email verification required
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    try:
        # Step 5: Save user to MongoDB
        # Beanie automatically creates the collection if it doesn't exist
        await new_user.insert()
    except Exception as e:
        # Handle database errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user. Please try again later.",
        ) from e

    # Step 6: Return success response
    return RegisterResponse(
        message="Registration successful! You can now login.",
        user_id=str(new_user.id),
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
    )
