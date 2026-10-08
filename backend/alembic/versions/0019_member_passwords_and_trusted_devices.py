"""Add member password sign-in and short-lived trusted-device records.

Revision ID: 0019_member_auth
Revises: 0018_linked_accounts
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_member_auth"
down_revision = "0018_linked_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable preserves existing demo and pilot users.  Only the new signup
    # endpoint creates password credentials; a later recovery flow can enrol
    # older accounts without inventing passwords for them.
    op.add_column("users", sa.Column("email", sa.String(), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(), nullable=True))
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(), nullable=True))
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "trusted_devices",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_trusted_devices_user_id", "trusted_devices", ["user_id"])
    op.create_index("ix_trusted_devices_expires_at", "trusted_devices", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_trusted_devices_expires_at", table_name="trusted_devices")
    op.drop_index("ix_trusted_devices_user_id", table_name="trusted_devices")
    op.drop_table("trusted_devices")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email")
