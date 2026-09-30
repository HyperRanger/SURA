"""add durable contact lookup rate limiting

Revision ID: 0013_contact_lookup_limit
Revises: 0012_bank_portal_operations
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_contact_lookup_limit"
down_revision = "0012_bank_portal_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contact_lookup_rate_limits",
        sa.Column("requester_user_id", sa.String(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("requester_user_id"),
    )


def downgrade() -> None:
    op.drop_table("contact_lookup_rate_limits")
