"""merge Lock lifecycle and certification migration paths

Revision ID: 0015_merge_lock_cert
Revises: 0014_lock_lifecycle, 0014_certification_schema
"""


revision = "0015_merge_lock_cert"
down_revision = ("0014_lock_lifecycle", "0014_certification_schema")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge-only revision: both parent migrations have already applied."""


def downgrade() -> None:
    """Merge-only revision: Alembic downgrades each parent separately."""
