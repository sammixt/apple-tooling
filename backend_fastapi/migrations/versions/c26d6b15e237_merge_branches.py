"""Merge branches

Revision ID: c26d6b15e237
Revises: 03d102f92ae1, 2c0f39b4af1b
Create Date: 2024-12-23 20:31:07.373778

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c26d6b15e237'
down_revision: Union[str, None] = ('03d102f92ae1', '2c0f39b4af1b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
