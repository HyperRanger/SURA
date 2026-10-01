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
    # SQLite cannot add a column with a foreign key via ALTER TABLE; the table
    # has to be recreated. batch_alter_table handles that on SQLite and emits
    # the plain ALTERs on PostgreSQL, so the resulting schema is identical.
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("role", sa.String(), nullable=False, server_default="individual"))
        batch.add_column(sa.Column("vendor_id", sa.String(), sa.ForeignKey("vendors.id", name="fk_users_vendor_id"), nullable=True))
        batch.add_column(sa.Column("context", sa.String(), nullable=True))
        batch.add_column(sa.Column("terms_accepted_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("phone_verified_at", sa.DateTime(), nullable=True))

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
