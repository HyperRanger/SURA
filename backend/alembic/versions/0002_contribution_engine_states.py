"""contribution engine states

Revision ID: 0002_contribution_engine_states
Revises: 0001_initial_schema
Create Date: 2026-09-26 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_contribution_engine_states"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contributions", sa.Column("status", sa.String(), nullable=False, server_default="full"))
    op.add_column("contributions", sa.Column("rule_trace_json", sa.Text(), nullable=False, server_default="{}"))
    # The original code emitted ALTER COLUMN ... DROP DEFAULT to remove the
    # temporary server_default above. PostgreSQL accepts that; SQLite does not
    # support ALTER COLUMN at all, so the whole migration failed there and left
    # `alembic upgrade head` unusable for local and CI verification.
    #
    # batch_alter_table rebuilds the table instead of altering it in place, which
    # works on both dialects. It renders no ALTER COLUMN when there is nothing
    # left to drop, so on PostgreSQL this is a no-op and the resulting schema is
    # unchanged.
    with op.batch_alter_table("contributions") as batch:
        batch.alter_column("status", server_default=None)
        batch.alter_column("rule_trace_json", server_default=None)

    # Same reason as above: SQLite cannot drop a constraint with ALTER, so this
    # runs inside the batch block, which recreates the table with the constraint
    # absent. On PostgreSQL batch mode is skipped and the plain DROP is emitted.
    with op.batch_alter_table("contributions") as batch:
        batch.drop_constraint("uq_contributions_commitment_cycle_user", type_="unique")


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade is irreversible: 0002 allows duplicate contribution rows per "
        "(commitment_id, cycle_number, user_id), so restoring the prior uniqueness "
        "constraint is unsafe without a manual data consolidation."
    )
