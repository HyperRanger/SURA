"""Add indexes for the API's hot Lock and redemption reads.

Revision ID: 0020_hot_read_indexes
Revises: 0019_member_auth
"""

from alembic import op


revision = "0020_hot_read_indexes"
down_revision = "0019_member_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_commitment_members_user_commitment",
        "commitment_members",
        ["user_id", "commitment_id"],
    )
    op.create_index(
        "ix_commitment_beneficiaries_commitment_cycle",
        "commitment_beneficiaries",
        ["commitment_id", "cycle_number"],
    )
    op.create_index(
        "ix_contributions_commitment_cycle_paid_user",
        "contributions",
        ["commitment_id", "cycle_number", "paid_at", "user_id"],
    )
    op.create_index(
        "ix_contributions_user_commitment",
        "contributions",
        ["user_id", "commitment_id"],
    )
    op.create_index(
        "ix_redemptions_vendor_redeemed",
        "redemptions",
        ["vendor_id", "redeemed_at"],
    )
    op.create_index(
        "ix_commitment_activities_commitment_occurred",
        "commitment_activities",
        ["commitment_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_commitment_activities_commitment_occurred", table_name="commitment_activities")
    op.drop_index("ix_redemptions_vendor_redeemed", table_name="redemptions")
    op.drop_index("ix_contributions_user_commitment", table_name="contributions")
    op.drop_index("ix_contributions_commitment_cycle_paid_user", table_name="contributions")
    op.drop_index("ix_commitment_beneficiaries_commitment_cycle", table_name="commitment_beneficiaries")
    op.drop_index("ix_commitment_members_user_commitment", table_name="commitment_members")
