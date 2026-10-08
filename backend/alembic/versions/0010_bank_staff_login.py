"""bank staff credentials for B1 sign-in

The Bank Portal signs people in with an email and password, which the phone-based
customer auth flow has no way to express. Credentials, the portal role and the
permission set live in one row owned by the bank domain, so revoking access is a
change to that table rather than an edit to a customer record.

Revision ID: 0010_bank_staff_login
Revises: 0009_merge_auth_and_bank_scope
"""

import sqlalchemy as sa

from alembic import op

revision = "0010_bank_staff_login"
down_revision = "0009_merge_auth_and_bank_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bank_staff",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("bank_id", sa.String(), sa.ForeignKey("bank_partners.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("permissions_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("mfa_phone", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("failed_password_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_bank_staff_bank_id", "bank_staff", ["bank_id"])
    op.create_index("ix_bank_staff_email", "bank_staff", ["email"])


def downgrade() -> None:
    op.drop_index("ix_bank_staff_email", table_name="bank_staff")
    op.drop_index("ix_bank_staff_bank_id", table_name="bank_staff")
    op.drop_table("bank_staff")
