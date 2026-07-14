from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends
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