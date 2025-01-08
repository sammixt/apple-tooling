"""empty message

Revision ID: c7fb9e8daa59
Revises: 86bea8dda1c4, ff8b323a47fb
Create Date: 2024-12-04 19:29:47.567752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7fb9e8daa59'
down_revision: Union[str, None] = ('86bea8dda1c4', 'ff8b323a47fb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
