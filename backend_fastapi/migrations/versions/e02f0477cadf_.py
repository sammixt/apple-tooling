"""empty message

Revision ID: e02f0477cadf
Revises: 52926ae7d3a4, b2d90aa1a8b2
Create Date: 2024-12-05 23:01:03.621820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e02f0477cadf'
down_revision: Union[str, None] = ('52926ae7d3a4', 'b2d90aa1a8b2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
