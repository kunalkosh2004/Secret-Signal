"""
FastAPI dependencies for authentication and authorization.

These are used in route handlers to protect endpoints.

TODO: Implement each dependency.

### Authentication (WHO are you?)

    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        Decode the JWT from the Authorization header.
        Look up the user by the `sub` claim.
        Raise UnauthorizedError if invalid or not found.

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
    This tells FastAPI to extract the token from the Authorization header:
        Authorization: Bearer <token>

### Authorization (WHAT are you allowed to do?)

    async def require_active_user(current_user: User = Depends(get_current_user)) -> User:
        Raise ForbiddenError if user.is_active is False.

    (Future) async def require_room_host(...) -> None:
        Check if the current user is the host of a specific room.

### Usage in routes:

    @router.get("/me")
    async def get_me(current_user: User = Depends(get_current_user)):
        return current_user
"""

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.security import decode_access_token
# from app.users.repository import user_repository
from app.users.models import User
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.users.repository import get_by_id


bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials

    payload = decode_access_token(token)

    if payload is None:
        raise UnauthorizedError()

    user_id = payload.get("sub")

    if user_id is None:
        raise UnauthorizedError()

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise UnauthorizedError()

    user = await get_by_id(db, user_id)

    if user is None:
        raise UnauthorizedError()

    return user

async def require_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise ForbiddenError()

    return current_user