"""
Security utilities — password hashing and JWT handling.

This module should contain PURE FUNCTIONS only:
    - hash_password(plaintext: str) -> str
    - verify_password(plaintext: str, hashed: str) -> bool
    - create_access_token(data: dict, expires_delta: timedelta | None) -> str
    - decode_access_token(token: str) -> dict | None

TODO: Implement each function below.

=== Password Hashing ===

Why not SHA-256?
    SHA-256 is designed to be FAST. Attackers can try billions of
    passwords per second with GPUs. Password hashing algorithms are
    designed to be SLOW and include a SALT.

What is a salt?
    A random value added to each password before hashing.
    It ensures the same password produces different hashes for different users.
    It prevents attackers from using pre-computed rainbow tables.

Algorithm choice:
    Use `bcrypt` (via the `passlib` library) or `argon2`.
    Both are well-tested password hashing algorithms.
    They handle salting automatically.

How to use passlib:
    pip install passlib[bcrypt]
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    pwd_context.hash(plaintext)       → hash
    pwd_context.verify(plaintext, hash) → bool

CryptContext notes:
    - `deprecated="auto"` will automatically upgrade old hashes.
    - You can later add new schemes and passlib handles migration.

=== JWT (JSON Web Token) ===

What is a JWT?
    A signed token containing a JSON payload.
    The signature proves the token was issued by your server (not tampered with).
    The PAYLOAD IS READABLE by anyone who has the token — never put secrets here.

Use python-jose or PyJWT:
    pip install pyjwt
    import jwt

    payload = {"sub": user_id, "exp": expiry_timestamp}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

Important:
    - ALWAYS set an `exp` (expiration) claim.
    - ALWAYS validate the signature.
    - Use the `sub` claim to store the user identifier (usually a UUID string).
    - Do NOT store passwords, roles as strings that could change, or secrets.
"""


# We'll use passlib for password hashing and PyJWT for tokens.
# Installation: pip install "passlib[bcrypt]" pyjwt

from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
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

    payload.update({"exp": expire})

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
