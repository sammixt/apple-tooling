"""activity_logs_feature

Revision ID: ad8edbfec4b5
Revises: c26d6b15e237
Create Date: 2024-12-24 16:54:04.088338

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ad8edbfec4b5"
down_revision: Union[str, None] = "c26d6b15e237"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    pass
    # op.create_table(
    #     "activity_logs",
    #     sa.Column("id", sa.Integer(), nullable=False),
    #     sa.Column("user_id", sa.Integer(), nullable=True),
    #     sa.Column("action", sa.String(), nullable=False),
    #     sa.Column("resource", sa.String(), nullable=False),
    #     sa.Column("resource_id", sa.String(), nullable=True),
    #     sa.Column("details", postgresql.JSONB(), nullable=True),
    #     sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    #     sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    #     sa.PrimaryKeyConstraint("id"),
    # )
    # op.create_index(op.f("ix_activity_logs_id"), "activity_logs", ["id"], unique=False)


def downgrade():
    pass
    # op.drop_table("activity_logs")
