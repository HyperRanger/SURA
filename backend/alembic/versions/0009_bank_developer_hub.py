"""add Bank Portal developer hub records

Revision ID: 0009_bank_developer_hub
Revises: 0008_score_history_bank_scope
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_bank_developer_hub"
down_revision = "0008_score_history_bank_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bank_api_keys",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("bank_id", sa.String(), sa.ForeignKey("bank_partners.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key_prefix", sa.String(), nullable=False),
        sa.Column("secret_hash", sa.String(), nullable=False),
        sa.Column("scopes_json", sa.Text(), nullable=False),
        sa.Column("environment", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_bank_api_keys_bank_id", "bank_api_keys", ["bank_id"])
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("bank_id", sa.String(), sa.ForeignKey("bank_partners.id"), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("event_types_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("signing_secret_hash", sa.String(), nullable=False),
        sa.Column("signing_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_webhook_subscriptions_bank_id", "webhook_subscriptions", ["bank_id"])
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("webhook_id", sa.String(), sa.ForeignKey("webhook_subscriptions.id"), nullable=False),
        sa.Column("bank_id", sa.String(), sa.ForeignKey("bank_partners.id"), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("signature", sa.String(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_webhook_deliveries_webhook_id", "webhook_deliveries", ["webhook_id"])
    op.create_index("ix_webhook_deliveries_bank_id", "webhook_deliveries", ["bank_id"])


def downgrade() -> None:
    op.drop_index("ix_webhook_deliveries_bank_id", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_webhook_id", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_index("ix_webhook_subscriptions_bank_id", table_name="webhook_subscriptions")
    op.drop_table("webhook_subscriptions")
    op.drop_index("ix_bank_api_keys_bank_id", table_name="bank_api_keys")
    op.drop_table("bank_api_keys")
