"""Add the bank-only balance snapshot used by the demo customer portfolio."""

from alembic import op
import sqlalchemy as sa


revision = "0016_demo_balance"
down_revision = "0015_merge_lock_cert"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("available_balance", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("users", "available_balance", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "available_balance")
