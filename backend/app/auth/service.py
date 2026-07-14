from app.auth.schemas import SignupRequest, LoginRequest, TokenResponse
from app.auth.security import hash_password, verify_password, create_access_token
from app.core.exceptions import ConflictError, UnauthorizedError
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.repository import (
    create,
    get_by_email,
    get_by_username,
)
from app.auth.oauth.google import verify_google_token
from app.auth.repository import (
    get_identity,
    create_identity,
)
from app.users.repository import (
    get_by_id,
)


async def generate_unique_username(
    db: AsyncSession,
    email: str,
) -> str:
    base_username = email.split("@")[0]

    # Keep username compatible with your 30-character limit
    base_username = base_username[:30]

    username = base_username
    counter = 1

    while await get_by_username(db, username) is not None:
        suffix = f"_{counter}"

        username = (
            base_username[: 30 - len(suffix)]
            + suffix
        )

        counter += 1

    return username


async def signup(
    db: AsyncSession,
    request: SignupRequest,
) -> TokenResponse:
    email = str(request.email).lower()

    existing_email = await get_by_email(db, email)

    if existing_email is not None:
        raise ConflictError()

    existing_username = await get_by_username(
        db,
        request.username,
    )

    if existing_username is not None:
        raise ConflictError()

    password_hash = hash_password(request.password)

    user = await create(
        db,
        username=request.username,
        email=email,
        password_hash=password_hash,
    )

    access_token = create_access_token(
        {
            "sub": str(user.id),
        }
    )

    return TokenResponse(
        access_token=access_token,
        user=user,
    )
  
async def login(
    db: AsyncSession,
    request: LoginRequest,
) -> TokenResponse:
    email = str(request.email).lower()

    user = await get_by_email(db, email)

    if user is None:
        raise UnauthorizedError()

    if user.password_hash is None:
        raise UnauthorizedError()

    password_is_valid = verify_password(
        request.password,
        user.password_hash,
    )

    if not password_is_valid:
        raise UnauthorizedError()

    access_token = create_access_token(
        {
            "sub": str(user.id),
        }
    )

    return TokenResponse(
        access_token=access_token,
        user=user,
    )

async def handle_google_callback(
    db: AsyncSession,
    code: str,
) -> TokenResponse:
    google_user = await verify_google_token(
        code=code,
    )

    # 1. Check whether this Google identity is already linked
    identity = await get_identity(
        db=db,
        provider="google",
        provider_subject=google_user.sub,
    )

    if identity is not None:
        user = await get_by_id(
            db,
            identity.user_id,
        )

        if user is None:
            raise UnauthorizedError()

        access_token = create_access_token(
            {
                "sub": str(user.id),
            }
        )

        return TokenResponse(
            access_token=access_token,
            user=user,
        )

    # 2. No Google identity exists.
    # Check whether the email already belongs to a local account.
    email = str(google_user.email).lower()

    existing_user = await get_by_email(
        db,
        email,
    )

    if existing_user is not None:
        # Your chosen policy:
        # do not automatically link Google to an existing account.
        raise ConflictError()

    # 3. Completely new user
    username = await generate_unique_username(
        db,
        email,
    )

    user = await create(
        db,
        username=username,
        email=email,
        password_hash=None,
        is_verified=google_user.email_verified,
    )

    # 4. Link Google identity to the new user
    await create_identity(
        db=db,
        user_id=user.id,
        provider="google",
        provider_subject=google_user.sub,
        provider_email=email,
    )

    # 5. Issue our application's JWT
    access_token = create_access_token(
        {
            "sub": str(user.id),
        }
    )

    return TokenResponse(
        access_token=access_token,
        user=user,
    )

async def handle_google_link_callback(
    db: AsyncSession,
    code: str,
    user_id: int,
) -> None:
    google_user = await verify_google_token(
        code=code,
    )

    # Check whether this Google account is already linked
    existing_identity = await get_identity(
        db=db,
        provider="google",
        provider_subject=google_user.sub,
    )

    if existing_identity is not None:
        raise ConflictError()

    # Get the authenticated local user
    user = await get_by_id(
        db,
        user_id,
    )

    if user is None:
        raise UnauthorizedError()

    # Optional but recommended for your chosen policy:
    # only link Google when its email matches the logged-in account.
    if user.email.lower() != str(google_user.email).lower():
        raise ConflictError()

    await create_identity(
        db=db,
        user_id=user.id,
        provider="google",
        provider_subject=google_user.sub,
        provider_email=str(google_user.email).lower(),
    )