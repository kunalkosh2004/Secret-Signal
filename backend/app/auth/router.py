"""
Authentication router — all /api/v1/auth/* endpoints.

Each handler is a stub that raises NotImplementedError.
Remove the stub and implement the real logic as you build each feature.

Endpoints:

    POST /signup
        Body: SignupRequest
        201: { user, access_token }
        409: email or username already exists
        422: validation error

    POST /login
        Body: LoginRequest
        200: { user, access_token }
        401: invalid credentials

    POST /logout
        200: logged out (or 204 No Content)
        May require authentication depending on token strategy.

    GET /me
        Header: Authorization: Bearer <token>
        200: UserResponse
        401: missing or invalid token

    GET /google/login
        302: redirect to Google consent screen

    GET /google/callback
        Query: code, state
        302: redirect to frontend with session
        401: OAuth error
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import secrets
from fastapi.responses import RedirectResponse
from fastapi import Query

from app.core.config import settings
from app.core.redis import (
    store_oauth_state,
    consume_oauth_state,
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
async def logout():
    """
    Log out the current user.

    With stateless JWT authentication, the client is responsible
    for deleting the access token.
    """
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