"""
SQLAlchemy User model.

TODO: Implement the User model.

Table:  users

Columns:
    id             UUID or auto-increment integer (primary key)
    username       String(30), unique, indexed, not null
    email          String(255), unique, indexed, not null
    password_hash  String(255), nullable  — null for users who only use Google OAuth
    is_active      Boolean, default True
    is_verified    Boolean, default False
    created_at     DateTime, server_default=func.now()
    updated_at     DateTime, onupdate=func.now()

Relationships:
    auth_identities  → list of AuthIdentity (defined in auth/ models later)

Constraints:
    - Unique constraint on username
    - Unique constraint on email

Never store plaintext passwords. password_hash stores only the output of
a secure password hashing function (bcrypt, argon2, etc.).
"""

from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column( 
        primary_key=True, 
        autoincrement=True
        )

    username: Mapped[str] = mapped_column(
        String(30), 
        unique=True, 
        index=True, 
        nullable=False
        )

    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True, 
        nullable=False
        )

    password_hash: Mapped[str] = mapped_column(
        String(255), 
        nullable=True
        )

    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False
        )

    is_verified: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False
        )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        nullable=False
        )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        onupdate=func.now(), 
        nullable=True
        )
