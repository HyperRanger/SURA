"""add bank customer references and auditable score inputs

Revision ID: 0006_bank_score_foundation
Revises: 0005_lock_app_contract
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_bank_score_foundation"
down_revision = "0005_lock_app_contract"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("users", sa.Column("bank_customer_id", sa.String(), nullable=True))
    op.create_index("ix_users_bank_customer_id", "users", ["bank_customer_id"])
    op.add_column("score_history", sa.Column("score_before", sa.Integer(), nullable=True))
    op.add_column("score_history", sa.Column("event_type", sa.String(), nullable=True))
    op.add_column("score_history", sa.Column("reason", sa.Text(), nullable=True))
    op.add_column("score_history", sa.Column("source_id", sa.String(), nullable=True))
    op.add_column("score_history", sa.Column("signals_json", sa.Text(), nullable=True))
    op.add_column("score_history", sa.Column("score_version", sa.String(), nullable=True))
    op.create_table("account_activity_signals",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("institution_id", sa.String(), sa.ForeignKey("institutions.id"), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_account_activity_signals_user_id", "account_activity_signals", ["user_id"])
    op.create_index("ix_account_activity_signals_institution_id", "account_activity_signals", ["institution_id"])

def downgrade() -> None:
    op.drop_index("ix_account_activity_signals_institution_id", table_name="account_activity_signals")
    op.drop_index("ix_account_activity_signals_user_id", table_name="account_activity_signals")
    op.drop_table("account_activity_signals")
    op.drop_column("score_history", "score_version")
    op.drop_column("score_history", "signals_json")
    op.drop_column("score_history", "source_id")
    op.drop_column("score_history", "reason")
    op.drop_column("score_history", "event_type")
    op.drop_column("score_history", "score_before")
    op.drop_index("ix_users_bank_customer_id", table_name="users")
    op.drop_column("users", "bank_customer_id")
