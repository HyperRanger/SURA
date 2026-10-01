"""add Bank Portal team and settings fields

Revision ID: 0012_bank_portal_operations
Revises: 0011_merge_bank_staff_dev
"""

import sqlalchemy as sa

from alembic import op

revision = "0012_bank_portal_operations"
down_revision = "0011_merge_bank_staff_dev"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bank_partners", sa.Column("environment", sa.String(), nullable=False, server_default="sandbox"))
    op.add_column("bank_partners", sa.Column("supported_vendor_categories_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("bank_partners", sa.Column("retention_days", sa.Integer(), nullable=False, server_default="365"))
    op.add_column("bank_partners", sa.Column("security_settings_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("bank_partners", sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("bank_partners", "updated_at")
    op.drop_column("bank_partners", "security_settings_json")
    op.drop_column("bank_partners", "retention_days")
    op.drop_column("bank_partners", "supported_vendor_categories_json")
    op.drop_column("bank_partners", "environment")
