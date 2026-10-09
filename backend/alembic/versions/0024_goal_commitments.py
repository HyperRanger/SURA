"""Add the declared target amount used by individual and collective goals.

Revision ID: 0024_goal_commitments
Revises: 0023_partner_links_payouts
"""

from alembic import op
import sqlalchemy as sa


revision = "0024_goal_commitments"
down_revision = "0023_partner_links_payouts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("commitments", sa.Column("target_amount", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("commitments", "target_amount")
