"""persist client contribution event IDs for retry safety

Revision ID: 0004_contribution_event_id
Revises: 0003_redemptions
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_contribution_event_id"
down_revision = "0003_redemptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contributions", sa.Column("event_id", sa.String(), nullable=True))
    op.execute("UPDATE contributions SET event_id = id WHERE event_id IS NULL")
    op.alter_column("contributions", "event_id", nullable=False)
    op.create_unique_constraint(
        "uq_contributions_commitment_user_event",
        "contributions",
        ["commitment_id", "user_id", "event_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_contributions_commitment_user_event", "contributions", type_="unique")
    op.drop_column("contributions", "event_id")
