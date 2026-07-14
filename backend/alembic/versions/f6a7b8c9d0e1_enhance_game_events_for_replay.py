"""enhance game_events for replay engine

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-14 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old index on user_id
    op.drop_index("ix_game_events_user_id", table_name="game_events")

    # Rename user_id to actor_id
    op.alter_column("game_events", "user_id", new_column_name="actor_id")

    # Recreate index on actor_id
    op.create_index(
        "ix_game_events_actor_id",
        "game_events",
        ["actor_id"],
        unique=False,
    )

    # Add sequence_number column with default
    op.add_column(
        "game_events",
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="0"),
    )

    # Add metadata column with default
    op.add_column(
        "game_events",
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
    )

    # Backfill sequence numbers for existing events per game
    op.execute("""
        WITH numbered AS (
            SELECT id, game_id,
                   ROW_NUMBER() OVER (PARTITION BY game_id ORDER BY id) AS rn
            FROM game_events
        )
        UPDATE game_events
        SET sequence_number = numbered.rn
        FROM numbered
        WHERE game_events.id = numbered.id
    """)

    # Drop server defaults now that data is backfilled
    op.alter_column("game_events", "sequence_number", server_default=None)
    op.alter_column("game_events", "metadata", server_default=None)

    # Create composite unique index on (game_id, sequence_number) AFTER backfill
    op.create_index(
        "ix_game_events_game_sequence",
        "game_events",
        ["game_id", "sequence_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_game_events_game_sequence", table_name="game_events")
    op.drop_column("game_events", "metadata")
    op.drop_column("game_events", "sequence_number")
    op.drop_index("ix_game_events_actor_id", table_name="game_events")
    op.alter_column("game_events", "actor_id", new_column_name="user_id")
    op.create_index(
        "ix_game_events_user_id",
        "game_events",
        ["user_id"],
        unique=False,
    )
