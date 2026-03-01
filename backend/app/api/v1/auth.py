"""Authentication endpoints for user registration, login, and token management."""

import secrets
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, status, HTTPException, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timezone, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...services.auth.utils import hash_password, verify_password
from ...services.auth.password_service import PasswordValidator
from ...services.auth.jwt_service import JWTService
from ...services.auth.pkce import verify_code_challenge
from ...models.auth import (
    ErrorResponse,
    RegisterRequest,
    RegisterResponse,
    AuthorizationCode,
    OAuth2Client,
    RefreshToken,
)
from ...models.user import User

# Create router for auth endpoints
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)

limiter = Limiter(key_func=get_remote_address)

# Jinja2 templates for server-rendered auth pages (login form, error page)
# Templates live at backend/app/templates/
templates_dir = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password. Password must contain uppercase, lowercase, number, and special character.",
)
@limiter.limit("5/minute")  # Limit to 5 registration attempts per minute per IP
async def register(request: Request, request_body: RegisterRequest) -> RegisterResponse:
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
    is_valid, error_message = PasswordValidator.validate(request_body.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Password validation failed",
                "detail": error_message,
            },
        )

    # Step 2: Check if email already exists (unique constraint)
    existing_user: Optional[User] = await User.find_one(
        User.email == request_body.email
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Email already registered",
                "detail": "An account with this email already exists.",
            },
        )

    # Step 3: Hash password
    password_hash = hash_password(request_body.password)

    # Step 4: Create new user document
    new_user = User(
        email=request_body.email,
        password_hash=password_hash,
        first_name=request_body.first_name,
        last_name=request_body.last_name,
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
            detail={
                "error": "Database error",
                "detail": "Failed to create user. Please try again later.",
            },
        ) from e

    # Step 6: Return success response
    return RegisterResponse(
        message="Registration successful! You can now login.",
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
    )


# ============================================================================
# OAuth2 Authorization Code + PKCE Endpoints (RFC 6749 §3.1, RFC 7636)
# ============================================================================
# Traditional OAuth2 flow using server-rendered login form:
#   1. GET  /authorize  — validate OAuth2 params, render login form
#   2. POST /login  — authenticate user, issue code, 302 redirect
#
# We use GET to serve the login form (as required by the spec) and POST
# to process the form submission (credentials never appear in URLs).
# ============================================================================
@router.get(
    "/authorize",
    response_class=HTMLResponse,
    summary="OAuth2 Authorization - Login Form",
    description=(
        "Validates OAuth2 + PKCE parameters and renders the authorization server's "
        "login form. The client redirects the user-agent here with OAuth2 params as "
        "query parameters (RFC 6749 §4.1.1, RFC 7636 §4.3)."
    ),
    include_in_schema=False,  # HTML page, not a JSON API — hide from OpenAPI docs
)
@limiter.limit("30/minute")
async def authorize_get(
    request: Request,
    response_type: str = Query(..., description="Must be 'code'"),
    client_id: str = Query(
        ..., min_length=1, max_length=128, description="OAuth2 client identifier"
    ),
    redirect_uri: str = Query(..., description="Must match a registered redirect URI"),
    code_challenge: str = Query(..., description="PKCE code challenge"),
    code_challenge_method: str = Query(
        default="S256", description="PKCE method — only S256 supported"
    ),
    scope: str = Query(default="", description="Space-delimited scopes"),
    state: str = Query(
        ..., min_length=32, max_length=128, description="CSRF state parameter"
    ),
) -> HTMLResponse:
    """
    OAuth2 Authorization Endpoint — GET (renders login form).

    Standard flow:
    1. Client redirects user-agent to this endpoint with OAuth2 query params
    2. Server validates client_id, redirect_uri, response_type, PKCE params
    3. Server renders HTML login form with OAuth2 params as hidden fields
    4. User submits credentials via POST to the same endpoint

    Error handling per RFC 6749 §4.1.2.1:
    - Invalid/missing client_id or redirect_uri → render error page (MUST NOT redirect)
    - Other errors → 302 redirect to redirect_uri with error query params
    """

    # ----------------------------------------------------------------
    # Step 1: Validate client_id
    # If client_id is invalid, MUST NOT redirect — show error page
    # ----------------------------------------------------------------
    client: Optional[OAuth2Client] = await OAuth2Client.find_one(
        OAuth2Client.client_id == client_id
    )
    if not client:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": "invalid_request", "detail": "Unknown client_id."},
            status_code=400,
        )

    if not client.is_active:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "error": "unauthorized_client",
                "detail": "This client has been deactivated.",
            },
            status_code=400,
        )

    # ----------------------------------------------------------------
    # Step 2: Validate redirect_uri
    # If redirect_uri is invalid, MUST NOT redirect — show error page
    # Simple string comparison per RFC 3986 §6.2.1
    # ----------------------------------------------------------------
    if redirect_uri not in client.redirect_uris:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "error": "invalid_request",
                "detail": "redirect_uri does not match any registered URI for this client.",
            },
            status_code=400,
        )

    # ----------------------------------------------------------------
    # From this point forward, client_id and redirect_uri are validated,
    # so errors are reported via 302 redirect to redirect_uri with
    # error query params
    # ----------------------------------------------------------------

    # Step 3: Validate response_type
    if response_type != "code":
        params = urlencode(
            {
                "error": "unsupported_response_type",
                "error_description": "response_type must be 'code'.",
                "state": state,
            }
        )
        return RedirectResponse(url=f"{redirect_uri}?{params}", status_code=302)

    # Step 4: Validate code_challenge_method
    # Only S256 — "plain" is discouraged
    if code_challenge_method != "S256":
        params = urlencode(
            {
                "error": "invalid_request",
                "error_description": "code_challenge_method must be 'S256'.",
                "state": state,
            }
        )
        return RedirectResponse(url=f"{redirect_uri}?{params}", status_code=302)

    # Step 5: Validate scopes
    if scope:
        requested_scopes = scope.split()
    else:
        requested_scopes = client.allowed_scopes

    invalid_scopes = [s for s in requested_scopes if s not in client.allowed_scopes]
    if invalid_scopes:
        params = urlencode(
            {
                "error": "invalid_scope",
                "error_description": f"Scopes not allowed: {', '.join(invalid_scopes)}",
                "state": state,
            }
        )
        return RedirectResponse(url=f"{redirect_uri}?{params}", status_code=302)

    # ----------------------------------------------------------------
    # Step 6: All OAuth2 params valid — render login form
    # Generate CSRF token: stored in httponly cookie + hidden form field
    # On POST, we compare them to prevent cross-site form submission
    # ----------------------------------------------------------------
    csrf_token = secrets.token_urlsafe(32)

    response = templates.TemplateResponse(
        request,
        "login.html",
        {
            "client_name": client.client_name,
            "scopes": requested_scopes,
            "response_type": response_type,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "csrf_token": csrf_token,
            "error": None,
            "email": "",
        },
    )

    # Set CSRF cookie — httponly so JavaScript cannot read it,
    # samesite=strict so it's only sent on same-origin requests
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        samesite="strict",
        secure=False,  # TODO: Set True in production (requires HTTPS)
        max_age=600,  # 10 minutes — enough time to fill the form
    )

    return response


@router.post(
    "/login",
    summary="OAuth2 Authorization - Process Login",
    description=(
        "Processes the login form submission. Validates CSRF token, authenticates "
        "the user, generates an authorization code, and redirects back to the "
        "client's redirect_uri with code + state (RFC 6749 §4.1.2)."
    ),
    include_in_schema=False,  # Form handler, not a JSON API
)
@limiter.limit("10/minute")  # Stricter rate limit — brute force protection
async def login(
    request: Request,
    # User credentials from form
    email: str = Form(...),
    password: str = Form(...),
    # OAuth2 parameters carried via hidden form fields
    response_type: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form(...),
    state: str = Form(...),
    scope: str = Form(default=""),
    # CSRF token from hidden form field
    csrf_token: str = Form(...),
):
    """
    OAuth2 Authorization Endpoint — POST (form submission handler).

    Standard flow:
    1. Verify CSRF token (cookie vs hidden field)
    2. Re-validate OAuth2 params (hidden fields can be tampered with)
    3. Authenticate user (email + password)
    4. Generate authorization code (256-bit entropy, RFC 6749 §10.10)
    5. Store AuthorizationCode with PKCE challenge (5 min TTL, RFC 7636 §4.4)
    6. 302 redirect to redirect_uri?code=...&state=... (RFC 6749 §4.1.2)

    On credential failure: re-render login form with error message.
    On OAuth2 param errors: redirect with error params or show error page.
    """

    # ----------------------------------------------------------------
    # Step 1: Verify CSRF token
    # Compare the httponly cookie value with the hidden form field.
    # Uses constant-time comparison to prevent timing attacks.
    # ----------------------------------------------------------------
    cookie_csrf = request.cookies.get("csrf_token")
    if not cookie_csrf or not secrets.compare_digest(cookie_csrf, csrf_token):
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "error": "invalid_request",
                "detail": "CSRF validation failed. Please try again.",
            },
            status_code=403,
        )

    # ----------------------------------------------------------------
    # Step 2: Re-validate client_id and redirect_uri
    # Hidden form fields can be tampered with by the user, so we must
    # re-validate before trusting them for the redirect
    # ----------------------------------------------------------------
    client: Optional[OAuth2Client] = await OAuth2Client.find_one(
        OAuth2Client.client_id == client_id
    )
    if not client or not client.is_active:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": "invalid_request", "detail": "Invalid or inactive client."},
            status_code=400,
        )

    if redirect_uri not in client.redirect_uris:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": "invalid_request", "detail": "Invalid redirect URI."},
            status_code=400,
        )

    # ----------------------------------------------------------------
    # Helper: re-render login form with error message on auth failure.
    # Generates a fresh CSRF token so the user can retry.
    # ----------------------------------------------------------------
    async def render_login_error(error_message: str):
        new_csrf = secrets.token_urlsafe(32)
        display_scopes = scope.split() if scope else client.allowed_scopes

        response = templates.TemplateResponse(
            request,
            "login.html",
            {
                "client_name": client.client_name,
                "scopes": display_scopes,
                "response_type": response_type,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": scope,
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": code_challenge_method,
                "csrf_token": new_csrf,
                "error": error_message,
                "email": email,  # Preserve email so user doesn't retype it
            },
            status_code=200,  # Not 401 — HTML pages should return 200
        )

        response.set_cookie(
            key="csrf_token",
            value=new_csrf,
            httponly=True,
            samesite="strict",
            secure=False,  # TODO: Set True in production
            max_age=600,
        )
        return response

    # ----------------------------------------------------------------
    # Step 3: Re-validate remaining OAuth2 params (tamper protection)
    # ----------------------------------------------------------------
    if response_type != "code":
        params = urlencode(
            {
                "error": "unsupported_response_type",
                "error_description": "response_type must be 'code'.",
                "state": state,
            }
        )
        return RedirectResponse(url=f"{redirect_uri}?{params}", status_code=302)

    if code_challenge_method != "S256":
        params = urlencode(
            {
                "error": "invalid_request",
                "error_description": "code_challenge_method must be 'S256'.",
                "state": state,
            }
        )
        return RedirectResponse(url=f"{redirect_uri}?{params}", status_code=302)

    if scope:
        requested_scopes = scope.split()
    else:
        requested_scopes = client.allowed_scopes

    invalid_scopes = [s for s in requested_scopes if s not in client.allowed_scopes]
    if invalid_scopes:
        params = urlencode(
            {
                "error": "invalid_scope",
                "error_description": f"Scopes not allowed: {', '.join(invalid_scopes)}",
                "state": state,
            }
        )
        return RedirectResponse(url=f"{redirect_uri}?{params}", status_code=302)

    # ----------------------------------------------------------------
    # Step 4: Authenticate user
    # Generic error prevents email enumeration
    # ----------------------------------------------------------------
    user: Optional[User] = await User.find_one(User.email == email)
    if not user or not verify_password(password, user.password_hash):
        return await render_login_error("Invalid email or password.")

    if not user.is_active:
        return await render_login_error("Account is deactivated.")

    if user.deleted_at is not None:
        return await render_login_error("Account has been deleted.")

    # ----------------------------------------------------------------
    # Step 5: Generate authorization code
    # Probability of guessing must be ≤ 2^(-128)
    # secrets.token_urlsafe(32) = 256-bit entropy
    # ----------------------------------------------------------------
    authorization_code = secrets.token_urlsafe(32)

    # ----------------------------------------------------------------
    # Step 6: Store AuthorizationCode with PKCE challenge
    # TTL: 5 minutes (RFC 6749 §10.5 recommends max 10 minutes)
    # ----------------------------------------------------------------
    now = datetime.now(timezone.utc)
    auth_code_doc = AuthorizationCode(
        user_id=str(user.id),
        code=authorization_code,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        state=state,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scopes=requested_scopes,
        created_at=now,
        expires_at=now + timedelta(minutes=5),
    )

    try:
        await auth_code_doc.insert()
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "error": "server_error",
                "detail": "Failed to create authorization code. Please try again.",
            },
            status_code=500,
        )

    # ----------------------------------------------------------------
    # Step 7: Update user's last_login timestamp
    # ----------------------------------------------------------------
    user.last_login = now
    await user.save()

    # ----------------------------------------------------------------
    # Step 8: 302 redirect to redirect_uri with code + state
    # (RFC 6749 §4.1.2 — Authorization Response)
    # Clear the CSRF cookie — it served its purpose
    # ----------------------------------------------------------------
    params = urlencode({"code": authorization_code, "state": state})
    response = RedirectResponse(url=f"{redirect_uri}?{params}", status_code=302)
    response.delete_cookie("csrf_token")
    return response


@router.post(
    "/token",
    summary="OAuth2 Token Endpoint",
    description=(
        "Exchanges an authorization code + code_verifier for JWT tokens. "
        "Validates PKCE proof, client credentials, and authorization code. "
        "Returns access_token (60 min TTL) and refresh_token (7 day TTL). "
        "(RFC 6749 §4.1.3, RFC 7636 §4.5)"
    ),
    include_in_schema=False,  # Token endpoint is not part of OpenAPI docs
)
@limiter.limit("10/minute")  # Rate limit to prevent brute force
async def token_exchange(
    request: Request,
    grant_type: str = Form(..., description="Must be 'authorization_code'"),
    client_id: str = Form(
        ..., description="Client ID (must match authorization request)"
    ),
    code: str = Form(..., description="Authorization code from /authorize endpoint"),
    code_verifier: str = Form(..., description="PKCE code_verifier (43-128 chars)"),
    redirect_uri: str = Form(
        ..., description="Redirect URI (must match authorization request)"
    ),
):
    """
    OAuth2 Token Endpoint (RFC 6749 §4.1.3, RFC 7636 §4.5).

    Exchanges authorization code + PKCE proof for JWT tokens.

    Flow:
    1. Validate grant_type == "authorization_code"
    2. Lookup and validate authorization code:
       - Code exists in database
       - Code has not expired (5 min TTL)
       - Code's client_id matches the provided client_id
       - Code's redirect_uri matches the provided redirect_uri
    3. Validate PKCE proof:
       - code_challenge_method must be "S256"
       - SHA256(code_verifier) must equal stored code_challenge
       - Prevents authorization code interception attacks
    4. Lookup user who authorized the code
    5. Generate JWT access token (60 min, HS256, RFC 7519 claims)
    6. Generate JWT refresh token (7 days, HS256)
    7. Delete used authorization code (prevent replay attacks)
    8. Return tokens as JSON

    Error Codes (RFC 6749 §5.2):
    - invalid_request: Missing or malformed parameters
    - unsupported_grant_type: grant_type != "authorization_code"
    - invalid_grant: Code invalid, expired, doesn't match client/redirect, or PKCE fails
    - invalid_client: Client not found or inactive

    Returns:
        JSON with access_token, token_type="Bearer", expires_in, refresh_token
    """

    # ----------------------------------------------------------------
    # Step 1: Validate grant_type (RFC 6749 §4.1.3 - REQUIRED)
    # ----------------------------------------------------------------
    if grant_type != "authorization_code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "unsupported_grant_type",
                "error_description": "grant_type must be 'authorization_code'.",
            },
        )

    # ----------------------------------------------------------------
    # Step 2: Lookup authorization code in database
    # ----------------------------------------------------------------
    auth_code_doc: Optional[AuthorizationCode] = await AuthorizationCode.find_one(
        AuthorizationCode.code == code
    )

    if not auth_code_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_grant",
                "error_description": "Authorization code is invalid.",
            },
        )

    # ----------------------------------------------------------------
    # Step 3: Validate code has not expired (5 min TTL)
    # ----------------------------------------------------------------
    now = datetime.now(timezone.utc)
    if auth_code_doc.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_grant",
                "error_description": "Authorization code has expired.",
            },
        )

    # ----------------------------------------------------------------
    # Step 4: Validate client_id matches
    # ----------------------------------------------------------------
    if auth_code_doc.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_grant",
                "error_description": "client_id does not match the authorization request.",
            },
        )

    # ----------------------------------------------------------------
    # Step 5: Validate redirect_uri matches
    # ----------------------------------------------------------------
    if auth_code_doc.redirect_uri != redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_grant",
                "error_description": "redirect_uri does not match the authorization request.",
            },
        )

    # ----------------------------------------------------------------
    # Step 6: Validate PKCE proof (RFC 7636 §4.5)
    # Verify that SHA256(code_verifier) == stored code_challenge
    # This proves the same entity that requested the code is exchanging it
    # ----------------------------------------------------------------
    if auth_code_doc.code_challenge_method != "S256":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_request",
                "error_description": "Unsupported code_challenge_method.",
            },
        )

    # Import PKCE verification function
    if not verify_code_challenge(code_verifier, auth_code_doc.code_challenge):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_grant",
                "error_description": "code_verifier does not match code_challenge.",
            },
        )

    # ----------------------------------------------------------------
    # Step 7: Lookup the user who authorized this code
    # ----------------------------------------------------------------
    user = await User.find_by_id(auth_code_doc.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "server_error",
                "detail": "User associated with authorization code not found.",
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_grant",
                "error_description": "User account is deactivated.",
            },
        )

    # ----------------------------------------------------------------
    # Step 8: Lookup OAuth2Client to verify it's still active
    # ----------------------------------------------------------------
    client: Optional[OAuth2Client] = await OAuth2Client.find_one(
        OAuth2Client.client_id == client_id
    )
    if not client or not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_client",
                "error_description": "Client is invalid or inactive.",
            },
        )

    # ----------------------------------------------------------------
    # Step 9: Generate access token (60 min TTL, HS256, RFC 7519)
    # Includes user_id, email, scopes, jti (token ID for revocation)
    # ----------------------------------------------------------------
    jwt_service = JWTService()
    access_token = jwt_service.create_access_token(
        user.id,
        email=user.email,
        scopes=auth_code_doc.scopes,
    )

    # ----------------------------------------------------------------
    # Step 10: Generate refresh token (7 day TTL, HS256, RFC 7519)
    # Used to get new access tokens without re-authenticating
    # ----------------------------------------------------------------
    refresh_token = jwt_service.create_refresh_token(
        user.id,
        email=user.email,
    )

    # ----------------------------------------------------------------
    # Step 11: Store RefreshToken document for revocation/tracking
    # Allows us to invalidate refresh tokens if needed
    # ----------------------------------------------------------------
    refresh_token_doc = RefreshToken(
        user_id=str(user.id),
        token=refresh_token,
        client_id=client_id,
        created_at=now,
        expires_at=now + timedelta(days=7),
    )

    try:
        await refresh_token_doc.insert()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "server_error",
                "detail": "Failed to store refresh token.",
            },
        ) from e

    # ----------------------------------------------------------------
    # Step 12: Delete used authorization code (prevent replay attacks)
    # Per RFC 6749 §10.5: "Authorization codes MUST be short-lived"
    # and "MUST NOT be issued to public clients"
    # ----------------------------------------------------------------
    try:
        await auth_code_doc.delete()
    except Exception as e:
        # Log but don't fail — token was already issued
        pass

    # ----------------------------------------------------------------
    # Step 13: Return token response (RFC 6749 §4.1.4)
    # access_token: JWT token for API requests
    # token_type: "Bearer" per RFC 6750 (OAuth 2.0 Bearer Token)
    # expires_in: Seconds until access_token expires (60 min = 3600 sec)
    # refresh_token: JWT for getting new access_token without re-auth
    # ----------------------------------------------------------------
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,  # 60 minutes in seconds
        "refresh_token": refresh_token,
    }
