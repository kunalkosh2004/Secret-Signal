from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
import uuid
from app.core.config import settings
from typing import Optional

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

def hash_password(plaintext: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(plaintext)


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plaintext, hashed)


def create_access_token(
        data: dict,
        expires_delta: Optional[int] = None,
    ) -> str:
    payload = data.copy()

    expire_minutes = (
        expires_delta
        if expires_delta is not None
        else settings.access_token_expire_minutes
    )

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expire_minutes
    )

    payload.update({
        "exp": expire,
        "jti": str(uuid.uuid4()),
    })

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None
