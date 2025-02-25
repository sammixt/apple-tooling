"""add batch as seperate table

Revision ID: 0d215c615047
Revises: 26ded442b835
Create Date: 2024-11-25 04:25:15.256128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d215c615047'
down_revision: Union[str, None] = '26ded442b835'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pre_processing_files', sa.Column('batch_id', sa.UUID(), nullable=True))
    op.create_foreign_key(None, 'pre_processing_files', 'batches', ['batch_id'], ['id'])
    op.add_column('validation_errors', sa.Column('batch_id', sa.UUID(), nullable=True))
    op.create_foreign_key(None, 'validation_errors', 'batches', ['batch_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'validation_errors', type_='foreignkey')
    op.drop_column('validation_errors', 'batch_id')
    op.drop_constraint(None, 'pre_processing_files', type_='foreignkey')
    op.drop_column('pre_processing_files', 'batch_id')
    # ### end Alembic commands ###
