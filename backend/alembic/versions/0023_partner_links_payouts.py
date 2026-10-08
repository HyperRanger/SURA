"""Add explicit partner-bank links and vendor payout labels.

Revision ID: 0023_partner_links_payouts
Revises: 0022_merge_catalogue_idle
"""

from alembic import op
import sqlalchemy as sa


revision = "0023_partner_links_payouts"
down_revision = "0022_merge_catalogue_idle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("linked_accounts", sa.Column("partner_bank_id", sa.String(), nullable=True))
    op.add_column("linked_accounts", sa.Column("shared_with_partner_at", sa.DateTime(), nullable=True))
    op.create_index("ix_linked_accounts_partner_bank_id", "linked_accounts", ["partner_bank_id"])
    op.create_foreign_key(
        "fk_linked_accounts_partner_bank_id",
        "linked_accounts",
        "bank_partners",
        ["partner_bank_id"],
        ["id"],
    )
    op.create_table(
        "vendor_payout_accounts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("vendor_id", sa.String(), nullable=False),
        sa.Column("bank_name", sa.String(), nullable=False),
        sa.Column("account_number_masked", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id"),
    )
    op.create_index("ix_vendor_payout_accounts_vendor_id", "vendor_payout_accounts", ["vendor_id"])


def downgrade() -> None:
    op.drop_index("ix_vendor_payout_accounts_vendor_id", table_name="vendor_payout_accounts")
    op.drop_table("vendor_payout_accounts")
    op.drop_constraint("fk_linked_accounts_partner_bank_id", "linked_accounts", type_="foreignkey")
    op.drop_index("ix_linked_accounts_partner_bank_id", table_name="linked_accounts")
    op.drop_column("linked_accounts", "shared_with_partner_at")
    op.drop_column("linked_accounts", "partner_bank_id")
