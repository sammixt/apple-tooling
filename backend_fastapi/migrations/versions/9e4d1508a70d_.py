"""empty message

Revision ID: 9e4d1508a70d
Revises: 3b283f9df99f, c7fb9e8daa59
Create Date: 2024-12-04 20:04:23.774816

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e4d1508a70d'
down_revision: Union[str, None] = ('3b283f9df99f', 'c7fb9e8daa59')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
