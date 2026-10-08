"""Track member last activity so idle sessions can be dropped server-side.

Revision ID: 0021_member_session_idle_timeout
Revises: 0020_hot_read_indexes
"""

from alembic import op
import sqlalchemy as sa


revision = "0021_member_session_idle_timeout"
down_revision = "0020_hot_read_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable on purpose: existing sessions have no activity record yet, and the
    # first authenticated request after deploy stamps the value.
    op.add_column("users", sa.Column("last_active_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_active_at")