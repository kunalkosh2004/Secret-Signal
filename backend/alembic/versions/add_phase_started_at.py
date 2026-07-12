"""add phase_started_at to games

Revision ID: a1b2c3d4e5f6
Revises: 98f1b7d2a5c3
Create Date: 2026-07-11 02:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '98f1b7d2a5c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('games', sa.Column('phase_started_at', sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    op.drop_column('games', 'phase_started_at')
