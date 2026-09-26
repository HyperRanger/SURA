"""contribution engine states

Revision ID: 0002_contribution_engine_states
Revises: 0001_initial_schema
Create Date: 2026-09-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_contribution_engine_states"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contributions", sa.Column("status", sa.String(), nullable=False, server_default="full"))
    op.add_column("contributions", sa.Column("rule_trace_json", sa.Text(), nullable=False, server_default="{}"))
    op.alter_column("contributions", "status", server_default=None)
    op.alter_column("contributions", "rule_trace_json", server_default=None)

    op.drop_constraint("uq_contributions_commitment_cycle_user", "contributions", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_contributions_commitment_cycle_user",
        "contributions",
        ["commitment_id", "cycle_number", "user_id"],
    )
    op.drop_column("contributions", "rule_trace_json")
    op.drop_column("contributions", "status")
