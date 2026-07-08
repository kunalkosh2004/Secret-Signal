"""
Auth repository — data-access for auth_identities and session data.

Planned table: auth_identities

    Columns:
        id:                  primary key
        user_id:             foreign key → users.id
        provider:            str   ("google", "apple", etc.)
        provider_subject:    str   (the stable ID from the provider)
        provider_email:      str   (email from provider, may change)
        created_at:          datetime

    Unique constraint on (provider, provider_subject)

Why is provider_subject better than email for identity linking?
    - The `sub` claim in OpenID Connect is a permanent, unique identifier
      for the user at the provider.
    - Emails can change. If a user changes their Google email, the `sub`
      stays the same, but the email doesn't.
    - Use email only as a convenience/display value.

TODO: Implement:

    async def get_identity(
        db: AsyncSession,
        provider: str,
        provider_subject: str,
    ) -> AuthIdentity | None

    async def create_identity(
        db: AsyncSession,
        user_id: UUID,
        provider: str,
        provider_subject: str,
        provider_email: str,
    ) -> AuthIdentity
"""

# TODO: from app.db.base import Base

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthIdentity


async def get_identity(
    db: AsyncSession,
    provider: str,
    provider_subject: str,
) -> Optional[AuthIdentity]:
    result = await db.execute(
        select(AuthIdentity).where(
            AuthIdentity.provider == provider,
            AuthIdentity.provider_subject == provider_subject,
        )
    )

    return result.scalar_one_or_none()


async def create_identity(
    db: AsyncSession,
    user_id: int,
    provider: str,
    provider_subject: str,
    provider_email: str,
) -> AuthIdentity:
    identity = AuthIdentity(
        user_id=user_id,
        provider=provider,
        provider_subject=provider_subject,
        provider_email=provider_email,
    )

    db.add(identity)

    await db.commit()
    await db.refresh(identity)

    return identity