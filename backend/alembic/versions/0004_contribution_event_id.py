"""persist client contribution event IDs for retry safety

Revision ID: 0004_contribution_event_id
Revises: 0003_redemptions
"""

import sqlalchemy as sa

from alembic import op

revision = "0004_contribution_event_id"
down_revision = "0003_redemptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contributions", sa.Column("event_id", sa.String(), nullable=True))
    op.execute("UPDATE contributions SET event_id = id WHERE event_id IS NULL")
    # SQLite cannot express ALTER COLUMN ... SET NOT NULL, and cannot add a
    # unique constraint with ALTER either. Both go through batch mode, which
    # recreates the table; on PostgreSQL the plain statements are emitted as
    # before and the resulting schema is identical.
    with op.batch_alter_table("contributions") as batch:
        batch.alter_column("event_id", nullable=False)
        batch.create_unique_constraint(
            "uq_contributions_commitment_user_event",
            ["commitment_id", "user_id", "event_id"],
        )


def downgrade() -> None:
    op.drop_constraint("uq_contributions_commitment_user_event", "contributions", type_="unique")
    op.drop_column("contributions", "event_id")
