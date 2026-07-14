"""
SQLAlchemy declarative base.

All models should inherit from this Base class.

Usage:
    from app.db.base import Base

    class User(Base):
        __tablename__ = "users"
        ...

Alembic discovers models by importing them so their metadata registers
on Base.metadata before the migration autogenerate runs.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
