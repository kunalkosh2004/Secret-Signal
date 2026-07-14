from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
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
