"""one-time codes, assigned roles, and a real signup/login path

Adds the challenge table behind POST /v1/auth/signup, /login and /verify-otp, and
records the role the backend assigns at signup so it can be carried in the token
and re-checked by protected endpoints.

Revision ID: 0008_auth_challenges
Revises: 0007_bank_portal_monitoring
"""

import sqlalchemy as sa

from alembic import op

revision = "0008_auth_challenges"
down_revision = "0007_bank_portal_monitoring"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(), nullable=False, server_default="individual"))
    op.add_column("users", sa.Column("vendor_id", sa.String(), sa.ForeignKey("vendors.id"), nullable=True))
    op.add_column("users", sa.Column("context", sa.String(), nullable=True))
    op.add_column("users", sa.Column("terms_accepted_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("phone_verified_at", sa.DateTime(), nullable=True))

    op.create_table(
        "auth_challenges",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("code_hash", sa.String(), nullable=False),
        sa.Column("salt", sa.String(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_auth_challenges_user_id", "auth_challenges", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_auth_challenges_user_id", table_name="auth_challenges")
    op.drop_table("auth_challenges")

    op.drop_column("users", "phone_verified_at")
    op.drop_column("users", "terms_accepted_at")
    op.drop_column("users", "vendor_id")
    op.drop_column("users", "context")
    op.drop_column("users", "role")
