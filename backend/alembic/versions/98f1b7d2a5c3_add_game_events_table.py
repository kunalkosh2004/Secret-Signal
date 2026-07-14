"""add game events table

Revision ID: 98f1b7d2a5c3
Revises: 8cd31e9f5658
Create Date: 2026-07-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "98f1b7d2a5c3"
down_revision: Union[str, Sequence[str], None] = "8cd31e9f5658"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "game_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_game_events_event_type"),
        "game_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_game_events_game_id"),
        "game_events",
        ["game_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_game_events_id"),
        "game_events",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_game_events_round_number"),
        "game_events",
        ["round_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_game_events_user_id"),
        "game_events",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_game_events_user_id"), table_name="game_events")
    op.drop_index(op.f("ix_game_events_round_number"), table_name="game_events")
    op.drop_index(op.f("ix_game_events_id"), table_name="game_events")
    op.drop_index(op.f("ix_game_events_game_id"), table_name="game_events")
    op.drop_index(op.f("ix_game_events_event_type"), table_name="game_events")
    op.drop_table("game_events")
