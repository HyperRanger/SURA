"""merge bank staff login and Developer Hub migration paths

Revision ID: 0011_merge_bank_staff_dev
Revises: 0010_bank_staff_login, 0010_merge_auth_developer
"""


revision = "0011_merge_bank_staff_dev"
down_revision = ("0010_bank_staff_login", "0010_merge_auth_developer")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """The parent migrations have already applied their schema changes."""


def downgrade() -> None:
    """Downgrades continue through the parent branches."""
