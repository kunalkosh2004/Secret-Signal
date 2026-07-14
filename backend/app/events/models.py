from sqlalchemy.sql import func
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Index,
)

from app.db.base import Base


class GameEvent(Base):
    __tablename__ = "game_events"

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

    sequence_number = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Deterministic ordering within a game. Replaces timestamp-based ordering for replay.",
    )

    round_number = Column(
        Integer,
        nullable=True,
        index=True,
    )

    event_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    actor_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="The user who performed this action (renamed from user_id for clarity).",
    )

    payload = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    event_metadata = Column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        comment="Additional context: timing, source, version info.",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_game_events_game_sequence",
            "game_id",
            "sequence_number",
            unique=True,
        ),
    )
