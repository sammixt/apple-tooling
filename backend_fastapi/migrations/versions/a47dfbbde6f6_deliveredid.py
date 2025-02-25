"""DeliveredId

Revision ID: a47dfbbde6f6
Revises: 252d68d09b40
Create Date: 2024-11-20 20:17:48.028664

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a47dfbbde6f6'
down_revision: Union[str, None] = '252d68d09b40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('delivered_ids',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deliverable_id', sa.String(length=100), nullable=False),
    sa.Column('project_name', sa.String(length=255), nullable=False),
    sa.Column('s3_path', sa.String(length=500), nullable=False),
    sa.Column('last_modified', sa.TIMESTAMP(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_delivered_ids_deliverable_id'), 'delivered_ids', ['deliverable_id'], unique=True)
    op.create_index(op.f('ix_delivered_ids_id'), 'delivered_ids', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_delivered_ids_id'), table_name='delivered_ids')
    op.drop_index(op.f('ix_delivered_ids_deliverable_id'), table_name='delivered_ids')
    op.drop_table('delivered_ids')
    # ### end Alembic commands ###
