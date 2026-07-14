from sqlalchemy.sql import func
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.db.base import Base


class TrainingMessage(Base):
    __tablename__ = "training_messages"

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

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    role = Column(
        String(30),
        nullable=False,
        index=True,
    )

    phase = Column(
        String(30),
        nullable=False,
        index=True,
    )

    content = Column(
        Text,
        nullable=False,
    )

    round_number = Column(
        Integer,
        nullable=True,
        index=True,
    )

    has_reply = Column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    reply_to_role = Column(
        String(30),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
