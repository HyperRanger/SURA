"""Add masked member funding-source labels.

Revision ID: 0018_linked_accounts
Revises: 0017_lock_group_policy
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_linked_accounts"
down_revision = "0017_lock_group_policy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "linked_accounts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("bank_name", sa.String(), nullable=False),
        sa.Column("account_number_masked", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_linked_accounts_user_id", "linked_accounts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_linked_accounts_user_id", table_name="linked_accounts")
    op.drop_table("linked_accounts")
