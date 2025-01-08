"""empty message

Revision ID: 6b84129bde89
Revises: bbba6d6c7f2b, bfdddbca5dcf
Create Date: 2024-11-15 02:18:54.889262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b84129bde89'
down_revision: Union[str, None] = ('bbba6d6c7f2b', 'bfdddbca5dcf')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
