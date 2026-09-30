"""merge authentication and Developer Hub migration branches

Revision ID: 0010_merge_auth_developer
Revises: 0008_auth_challenges, 0009_bank_developer_hub
"""


revision = "0010_merge_auth_developer"
down_revision = ("0008_auth_challenges", "0009_bank_developer_hub")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Both parent migrations have already applied their schema changes."""


def downgrade() -> None:
    """Downgrades continue through the parent branches."""
