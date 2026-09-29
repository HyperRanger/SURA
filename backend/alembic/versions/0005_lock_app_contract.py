"""add Sura Lock app consent, activity, and voucher records

Revision ID: 0005_lock_app_contract
Revises: 0004_contribution_event_id
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_lock_app_contract"
down_revision = "0004_contribution_event_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_consents",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("consent_type", sa.String(), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "consent_type", name="uq_user_consents_user_type"),
    )
    op.create_table(
        "commitment_activities",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("commitment_id", sa.String(), sa.ForeignKey("commitments.id"), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("actor_user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("cycle_number", sa.Integer(), nullable=True),
        sa.Column("detail_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "vouchers",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("commitment_id", sa.String(), sa.ForeignKey("commitments.id"), nullable=False),
        sa.Column("beneficiary_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vendor_id", sa.String(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("cycle_number", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="ready"),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("redeemed_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("commitment_id", "cycle_number", name="uq_vouchers_commitment_cycle"),
        sa.UniqueConstraint("code", name="uq_vouchers_code"),
    )


def downgrade() -> None:
    op.drop_table("vouchers")
    op.drop_table("commitment_activities")
    op.drop_table("user_consents")
