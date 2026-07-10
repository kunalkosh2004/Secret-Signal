from sqlalchemy.sql import func
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from app.db.base import Base


class Mission(Base):
    __tablename__ = "missions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    assigned_to_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    mission_type = Column(
        String(50),
        nullable=False,
    )

    title = Column(
        String(100),
        nullable=False,
    )

    description = Column(
        String(500),
        nullable=False,
    )

    target_value = Column(
        Integer,
        nullable=False,
    )

    current_value = Column(
        Integer,
        nullable=False,
        default=0,
    )

    status = Column(
        String(20),
        nullable=False,
        default="active",
    )

    round_number = Column(
        Integer,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )