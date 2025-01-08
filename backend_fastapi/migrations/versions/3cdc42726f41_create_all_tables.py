"""Create all tables

Revision ID: 3cdc42726f41
Revises: 8039e9cc6f43
Create Date: 2024-10-25 10:13:12.242084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3cdc42726f41'
down_revision: Union[str, None] = '8039e9cc6f43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('google_auth_id', sa.String(), nullable=True),
        sa.Column('email', sa.String(), unique=True, nullable=False),
        sa.Column('profile_pic_url', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Create the s3_files table
    op.create_table(
        's3_files',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('s3key', sa.String(), unique=True, index=True, nullable=False),
        sa.Column('file_url', sa.String(), nullable=False),
        sa.Column('workstream', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Create the file_stats table
    op.create_table(
        'file_stats',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('s3file_id', sa.Integer(), sa.ForeignKey('s3_files.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stats_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Create the file_contents table
    op.create_table(
        'file_contents',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('s3file_id', sa.Integer(), sa.ForeignKey('s3_files.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', postgresql.JSONB(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Create the file_validations table
    op.create_table(
        'file_validations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('s3file_id', sa.Integer(), sa.ForeignKey('s3_files.id', ondelete='CASCADE'), nullable=False),
        sa.Column('validation_type', sa.String(), nullable=False),
        sa.Column('validation_errors', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.UniqueConstraint('s3file_id', 'validation_type', name='uq_s3file_validation_type'),
    )


def downgrade() -> None:
    # Drop the file_validations table
    op.drop_table('file_validations')

    # Drop the file_contents table
    op.drop_table('file_contents')

    # Drop the file_stats table
    op.drop_table('file_stats')

    # Drop the s3_files table
    op.drop_table('s3_files')

    # Drop the users table
    op.drop_table('users')
