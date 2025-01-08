"""Merged heads

Revision ID: 87f0a00ca0c2
Revises: 4914e0271253, 57368b305619
Create Date: 2024-12-31 10:24:51.963445

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87f0a00ca0c2'
down_revision: Union[str, None] = ('4914e0271253', '57368b305619')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
