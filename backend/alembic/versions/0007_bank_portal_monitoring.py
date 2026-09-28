"""add bank tenant, monitoring, risk flags, and bank audit records

Revision ID: 0007_bank_portal_monitoring
Revises: 0006_bank_score_foundation
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_bank_portal_monitoring"
down_revision = "0006_bank_score_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bank_partners",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.add_column("users", sa.Column("bank_id", sa.String(), nullable=True))
    op.create_foreign_key("fk_users_bank_id", "users", "bank_partners", ["bank_id"], ["id"])
    op.create_index("ix_users_bank_id", "users", ["bank_id"])
    op.create_table(
        "risk_flags",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("bank_id", sa.String(), sa.ForeignKey("bank_partners.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rule", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("evidence_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_risk_flags_bank_id", "risk_flags", ["bank_id"])
    op.create_index("ix_risk_flags_user_id", "risk_flags", ["user_id"])
    op.create_table(
        "bank_audit_events",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("bank_id", sa.String(), sa.ForeignKey("bank_partners.id"), nullable=False),
        sa.Column("actor_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("subject_type", sa.String(), nullable=False),
        sa.Column("subject_id", sa.String(), nullable=False),
        sa.Column("detail_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_bank_audit_events_bank_id", "bank_audit_events", ["bank_id"])


def downgrade() -> None:
    op.drop_index("ix_bank_audit_events_bank_id", table_name="bank_audit_events")
    op.drop_table("bank_audit_events")
    op.drop_index("ix_risk_flags_user_id", table_name="risk_flags")
    op.drop_index("ix_risk_flags_bank_id", table_name="risk_flags")
    op.drop_table("risk_flags")
    op.drop_index("ix_users_bank_id", table_name="users")
    op.drop_constraint("fk_users_bank_id", "users", type_="foreignkey")
    op.drop_column("users", "bank_id")
    op.drop_table("bank_partners")
