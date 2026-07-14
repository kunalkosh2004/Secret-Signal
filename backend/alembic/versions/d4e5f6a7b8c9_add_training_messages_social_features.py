"""add_training_messages_social_features

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-14 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "training_messages",
        sa.Column(
            "has_reply",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.add_column(
        "training_messages",
        sa.Column(
            "reply_to_role",
            sa.String(30),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("training_messages", "reply_to_role")
    op.drop_column("training_messages", "has_reply")
