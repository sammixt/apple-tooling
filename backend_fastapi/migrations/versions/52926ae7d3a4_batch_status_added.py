"""batch status added

Revision ID: 52926ae7d3a4
Revises: 121796f51905
Create Date: 2024-12-05 12:39:58.164704

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_postgresql_enum import TableReference

# revision identifiers, used by Alembic.
revision: str = '52926ae7d3a4'
down_revision: Union[str, None] = '121796f51905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('batches', sa.Column('failed_reason', sa.String(), nullable=True))
    op.sync_enum_values(
        enum_schema='public',
        enum_name='statusenum',
        new_values=['IN_PROGRESS', 'COMPLETED', 'FAILED'],
        affected_columns=[TableReference(table_schema='public', table_name='batches', column_name='status')],
        enum_values_to_rename=[],
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.sync_enum_values(
        enum_schema='public',
        enum_name='statusenum',
        new_values=['IN_PROGRESS', 'COMPLETED'],
        affected_columns=[TableReference(table_schema='public', table_name='batches', column_name='status')],
        enum_values_to_rename=[],
    )
    op.drop_column('batches', 'failed_reason')
    # ### end Alembic commands ###
