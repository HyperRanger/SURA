"""record why each score changed, not just what it changed to

Revision ID: 0005_score_history_audit
Revises: 0004_contribution_event_id
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_score_history_audit"
down_revision = "0004_contribution_event_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("score_history", sa.Column("old_score", sa.Integer(), nullable=True))
    op.add_column("score_history", sa.Column("event_id", sa.String(), nullable=True))
    op.add_column("score_history", sa.Column("reason", sa.String(), nullable=True))
    op.create_index("ix_score_history_user_computed", "score_history", ["user_id", "computed_at"])


def downgrade() -> None:
    op.drop_index("ix_score_history_user_computed", table_name="score_history")
    op.drop_column("score_history", "reason")
    op.drop_column("score_history", "event_id")
    op.drop_column("score_history", "old_score")
