"""Add the explicit rotating-Lock missed-cycle policy.

Revision ID: 0017_lock_group_policy
Revises: 0016_demo_balance
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_lock_group_policy"
down_revision = "0016_demo_balance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "commitments",
        sa.Column(
            "missed_cycle_policy",
            sa.String(),
            nullable=False,
            server_default="carry_forward",
        ),
    )
    # The October demo has one disclosed grace window. Normalising existing
    # rows prevents old per-row values from changing how the same screen reads
    # a commitment after the release.
    op.execute("UPDATE commitments SET grace_period_hours = 72")
    op.alter_column("commitments", "missed_cycle_policy", server_default=None)


def downgrade() -> None:
    op.drop_column("commitments", "missed_cycle_policy")
