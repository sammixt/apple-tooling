"""remove workstream and created enum

Revision ID: 685500b8e8d3
Revises: 88f25f2119c6
Create Date: 2024-12-04 04:04:32.922108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '685500b8e8d3'
down_revision: Union[str, None] = '88f25f2119c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    sa.Enum('RLHF_VISION', 'IMAGE_EVAL', name='workstreamenum').create(op.get_bind())
    op.add_column('batches', sa.Column('workstream', postgresql.ENUM('RLHF_VISION', 'IMAGE_EVAL', name='workstreamenum', create_type=False), nullable=True))
    op.drop_constraint('batches_workstream_id_fkey', 'batches', type_='foreignkey')
    op.drop_column('batches', 'workstream_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('batches', sa.Column('workstream_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('batches_workstream_id_fkey', 'batches', 'workstream', ['workstream_id'], ['id'])
    op.drop_column('batches', 'workstream')
    sa.Enum('RLHF_VISION', 'IMAGE_EVAL', name='workstreamenum').drop(op.get_bind())
    # ### end Alembic commands ###
