"""add vendor locked redemptions

Revision ID: 0003_redemptions
Revises: 0002_contribution_engine_states
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa

revision = "0003_redemptions"
down_revision = "0002_contribution_engine_states"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "redemptions",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("commitment_id", sa.String(), sa.ForeignKey("commitments.id"), nullable=False),
        sa.Column("beneficiary_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vendor_id", sa.String(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("cycle_number", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("voucher_code", sa.String(), nullable=False, unique=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("commitment_id", "cycle_number", name="uq_redemptions_commitment_cycle"),
    )
    op.bulk_insert(
        sa.table(
            "vendors",
            sa.column("id", sa.String()),
            sa.column("name", sa.String()),
            sa.column("category", sa.String()),
            sa.column("verified_at", sa.DateTime()),
        ),
        [
            {"id": "vnd_demo_electronics", "name": "Sura Demo Electronics", "category": "electronics", "verified_at": datetime.utcnow()},
            {"id": "vnd_demo_education", "name": "Sura Demo Education", "category": "education", "verified_at": datetime.utcnow()},
            {"id": "vnd_demo_equipment", "name": "Sura Demo Equipment", "category": "equipment", "verified_at": datetime.utcnow()},
        ],
    )


def downgrade() -> None:
    op.drop_table("redemptions")
