"""Merge branches

Revision ID: 2c0f39b4af1b
Revises: b1dd36581396, ebdd772d11b6
Create Date: 2024-12-20 19:34:43.534203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c0f39b4af1b'
down_revision: Union[str, None] = ('b1dd36581396', 'ebdd772d11b6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
