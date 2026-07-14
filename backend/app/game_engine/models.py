from sqlalchemy.sql import func
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)

from app.db.base import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="active",
    )

    round_number = Column(
        Integer,
        nullable=False,
        default=1,
    )

    phase = Column(
        String(30),
        nullable=False,
        default="role_assignment",
    )

    max_rounds = Column(
        Integer,
        nullable=False,
        default=1,
    )

    phase_durations = Column(
        JSON,
        nullable=False,
        server_default="{}",
    )

    phase_started_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class GamePlayer(Base):
    __tablename__ = "game_players"

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
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role = Column(
        String(30),
        nullable=False,
    )

    score = Column(
        Integer,
        nullable=False,
        default=0,
    )

    joined_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "user_id",
            name="uq_game_player",
        ),
    )