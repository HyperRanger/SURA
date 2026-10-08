"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-25 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("fee_calendar_json", sa.Text(), nullable=True),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("institution_id", sa.String(), sa.ForeignKey("institutions.id"), nullable=True),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("phone", name="uq_users_phone"),
    )
    op.create_table(
        "vendors",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "commitments",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("creator_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(), nullable=False, server_default="rotating"),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("vendor_id", sa.String(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("contribution_amount", sa.Integer(), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("cycles", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending_members"),
        sa.Column("invite_code", sa.String(), nullable=False),
        sa.Column("payout_order_json", sa.Text(), nullable=False),
        sa.Column("current_cycle_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("completed_cycle_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("invite_code", name="uq_commitments_invite_code"),
    )
    op.create_table(
        "commitment_members",
        sa.Column("commitment_id", sa.String(), sa.ForeignKey("commitments.id"), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), primary_key=True, nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="contributor"),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "commitment_beneficiaries",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("commitment_id", sa.String(), sa.ForeignKey("commitments.id"), nullable=False),
        sa.Column("cycle_number", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("payout_amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="scheduled"),
    )
    op.create_table(
        "contributions",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("commitment_id", sa.String(), sa.ForeignKey("commitments.id"), nullable=False),
        sa.Column("cycle_number", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("commitment_id", "cycle_number", "user_id", name="uq_contributions_commitment_cycle_user"),
    )
    op.create_table(
        "score_history",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("breakdown_json", sa.Text(), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("score_history")
    op.drop_table("contributions")
    op.drop_table("commitment_beneficiaries")
    op.drop_table("commitment_members")
    op.drop_table("commitments")
    op.drop_table("vendors")
    op.drop_table("users")
    op.drop_table("institutions")