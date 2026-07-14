from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
from fastapi.responses import RedirectResponse
from fastapi import Query

from app.core.config import settings
from app.core.redis import (
    store_oauth_state,
    consume_oauth_state,
    revoke_token,
    store_password_reset_token,
    consume_password_reset_token,
    revoke_all_user_tokens,
)
from app.core.exceptions import UnauthorizedError
from app.auth.schemas import SignupRequest, LoginRequest, TokenResponse
from app.auth.service import (
    signup as signup_service,
    login as login_service,
    handle_google_callback
)
from app.db.session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.users.schemas import UserResponse
from app.auth.oauth.google import build_authorization_url
from app.core.redis import store_google_link_state
from app.auth.service import handle_google_link_callback
from app.core.redis import consume_google_link_state
from app.auth.security import decode_access_token
from app.core.redis_rate_limit import is_rate_limited
from pydantic import BaseModel
from app.users import repository as user_repository
from app.auth.security import hash_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/signup",
    status_code=201,
    response_model=TokenResponse,
)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    return await signup_service(db, request)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await login_service(db, request)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Log out the current user by revoking their JWT token.
    """
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "").strip()

    if token:
        payload = decode_access_token(token)
        if payload:
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                import time
                remaining = max(0, int(exp) - int(time.time()))
                await revoke_token(jti, remaining)

    return {
        "message": "Logged out successfully"
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get("/google/login")
async def google_login():
    state = secrets.token_urlsafe(32)

    await store_oauth_state(state)

    authorization_url = build_authorization_url(state)

    return RedirectResponse(
        url=authorization_url,
        status_code=302,
    )


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    state_is_valid = await consume_oauth_state(state)

    if not state_is_valid:
        raise UnauthorizedError()

    result = await handle_google_callback(
        db=db,
        code=code
    )

    return RedirectResponse(
        url=f"{settings.frontend_url}/auth/google/callback?access_token={result.access_token}",
        status_code=302,
    )

@router.get("/google/link")
async def google_link(
    current_user: User = Depends(get_current_user),
):
    state = secrets.token_urlsafe(32)

    await store_google_link_state(
        state=state,
        user_id=current_user.id,
    )

    authorization_url = build_authorization_url(
        state=state,
        redirect_uri=settings.google_link_redirect_uri,
    )

    return RedirectResponse(
        url=authorization_url,
        status_code=302,
    )

@router.get("/google/link/callback")
async def google_link_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user_id = await consume_google_link_state(state)

    if user_id is None:
        raise UnauthorizedError()

    await handle_google_link_callback(
        db=db,
        code=code,
        user_id=user_id,
    )

    return {
        "message": "Google account linked successfully"
    }


# ---------------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------------

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a password reset token.
    In production, this would send an email. For now, we return the token directly.
    """
    # Rate limit: 3 forgot password requests per minute per email
    if await is_rate_limited("api_auth", f"forgot:{request.email}", max_requests=3, window_seconds=60):
        raise UnauthorizedError("Too many requests. Please wait before trying again.")

    user = await user_repository.get_by_email(db, request.email.lower().strip())

    if user is None:
        # Don't reveal whether the email exists
        return {"message": "If an account with that email exists, a reset link has been sent."}

    # Generate a secure reset token
    reset_token = secrets.token_urlsafe(32)
    await store_password_reset_token(user.id, reset_token)

    # In production: send email with reset_token
    # For now: return token in response (development only)
    return {
        "message": "If an account with that email exists, a reset link has been sent.",
        "reset_token": reset_token,  # Remove in production
    }


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using a valid reset token."""
    user_id = await consume_password_reset_token(request.token)

    if user_id is None:
        raise UnauthorizedError("Invalid or expired reset token.")

    # Validate new password
    if len(request.new_password) < 8:
        raise UnauthorizedError("Password must be at least 8 characters.")

    user = await user_repository.get_by_id(db, user_id)
    if user is None:
        raise UnauthorizedError("User not found.")

    # Update password
    user.password_hash = hash_password(request.new_password)
    await db.commit()

    # Revoke all existing tokens for this user
    await revoke_all_user_tokens(user_id, expires_in_seconds=3600)

    return {"message": "Password reset successfully. Please log in with your new password."}