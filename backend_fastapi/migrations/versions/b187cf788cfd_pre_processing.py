"""pre_processing

Revision ID: b187cf788cfd
Revises: 3cdc42726f41
Create Date: 2024-11-07 01:50:34.127785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b187cf788cfd'
down_revision: Union[str, None] = '3cdc42726f41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Pre Processing Files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_Pre Processing Files_id'), 'Pre Processing Files', ['id'], unique=False)
    op.alter_column('file_contents', 'content',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=sa.JSON(),
               existing_nullable=False)
    op.drop_constraint('file_contents_s3file_id_fkey', 'file_contents', type_='foreignkey')
    op.create_foreign_key(None, 'file_contents', 's3_files', ['s3file_id'], ['id'])
    op.alter_column('file_stats', 'stats_data',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=sa.JSON(),
               existing_nullable=False)
    op.drop_constraint('file_stats_s3file_id_fkey', 'file_stats', type_='foreignkey')
    op.create_foreign_key(None, 'file_stats', 's3_files', ['s3file_id'], ['id'])
    op.alter_column('file_validations', 'validation_errors',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=sa.JSON(),
               existing_nullable=True)
    op.drop_constraint('file_validations_s3file_id_fkey', 'file_validations', type_='foreignkey')
    op.create_foreign_key(None, 'file_validations', 's3_files', ['s3file_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'file_validations', type_='foreignkey')
    op.create_foreign_key('file_validations_s3file_id_fkey', 'file_validations', 's3_files', ['s3file_id'], ['id'], ondelete='CASCADE')
    op.alter_column('file_validations', 'validation_errors',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True)
    op.drop_constraint(None, 'file_stats', type_='foreignkey')
    op.create_foreign_key('file_stats_s3file_id_fkey', 'file_stats', 's3_files', ['s3file_id'], ['id'], ondelete='CASCADE')
    op.alter_column('file_stats', 'stats_data',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=False)
    op.drop_constraint(None, 'file_contents', type_='foreignkey')
    op.create_foreign_key('file_contents_s3file_id_fkey', 'file_contents', 's3_files', ['s3file_id'], ['id'], ondelete='CASCADE')
    op.alter_column('file_contents', 'content',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=False)
    op.drop_index(op.f('ix_Pre Processing Files_id'), table_name='Pre Processing Files')
    op.drop_table('Pre Processing Files')
    # ### end Alembic commands ###
