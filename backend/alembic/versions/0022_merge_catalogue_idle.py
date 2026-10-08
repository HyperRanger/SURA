"""Merge the vendor catalogue and member idle-session migration paths.

Both changes were developed from ``0020_hot_read_indexes`` and are independent.
This revision intentionally has no schema operations: it records that a database
at either branch must apply the other branch before it is considered current.

Revision ID: 0022_merge_catalogue_idle
Revises: 0021_vendor_catalogue, 0021_member_session_idle_timeout
"""


revision = "0022_merge_catalogue_idle"
down_revision = ("0021_vendor_catalogue", "0021_member_session_idle_timeout")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Join independent migration paths without changing the schema."""


def downgrade() -> None:
    """Split the migration graph without changing the schema."""

