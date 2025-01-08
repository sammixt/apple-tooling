"""Added annotator id in s3files

Revision ID: bfdddbca5dcf
Revises: cca612c9abca
Create Date: 2024-11-14 13:43:46.606468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfdddbca5dcf'
down_revision: Union[str, None] = 'cca612c9abca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Add the annotator_id column ###
    op.add_column('s3_files', sa.Column('annotator_id', sa.Integer(), nullable=True))
    op.create_index('ix_s3files_annotator_id', 's3_files', ['annotator_id'])

def downgrade() -> None:
    # ### Remove the annotator_id column ###
    op.drop_index('ix_s3files_annotator_id', table_name='s3_files')
    op.drop_column('s3_files', 'annotator_id')