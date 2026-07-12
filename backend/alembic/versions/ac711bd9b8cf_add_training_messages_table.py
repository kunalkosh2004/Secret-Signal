"""add_training_messages_table

Revision ID: ac711bd9b8cf
Revises: a1b2c3d4e5f6
Create Date: 2026-07-11 01:33:31.723403

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac711bd9b8cf'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "training_messages",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "game_id",
            sa.Integer(),
            sa.ForeignKey("games.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("role", sa.String(30), nullable=False, index=True),
        sa.Column("phase", sa.String(30), nullable=False, index=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=True, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("training_messages")
