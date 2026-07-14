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