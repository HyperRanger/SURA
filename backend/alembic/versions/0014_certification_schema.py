"""certification: session revocations, member session invalidation, restriction columns

Revision ID: 0014_certification_schema
Revises: 0013_contact_lookup_limit
"""

import sqlalchemy as sa

from alembic import op

revision = "0014_certification_schema"
down_revision = "0013_contact_lookup_limit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_audit_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("actor_id", sa.String(), nullable=True),
        sa.Column("actor_role", sa.String(), nullable=True),
        sa.Column("institution_id", sa.String(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("subject_type", sa.String(), nullable=False),
        sa.Column("subject_id", sa.String(), nullable=False),
        sa.Column("detail_json", sa.Text(), nullable=False),
        sa.Column("source_ip", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_platform_audit_events_institution_id"),
        "platform_audit_events",
        ["institution_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_platform_audit_events_event_type"),
        "platform_audit_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_platform_audit_events_occurred_at"),
        "platform_audit_events",
        ["occurred_at"],
        unique=False,
    )

    op.create_table(
        "session_revocations",
        sa.Column("jti", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("jti"),
    )
    op.create_index(
        op.f("ix_session_revocations_user_id"),
        "session_revocations",
        ["user_id"],
        unique=False,
    )

    op.add_column(
        "users",
        sa.Column("session_invalidated_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("account_status", sa.String(), nullable=False, server_default="active"),
    )
    op.add_column("users", sa.Column("restriction_reason", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("restricted_by", sa.String(), nullable=True))
    op.add_column("users", sa.Column("restricted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "restricted_at")
    op.drop_column("users", "restricted_by")
    op.drop_column("users", "restriction_reason")
    op.drop_column("users", "account_status")
    op.drop_column("users", "session_invalidated_at")
    op.drop_index(
        op.f("ix_session_revocations_user_id"),
        table_name="session_revocations",
    )
    op.drop_table("session_revocations")
    op.drop_index(
        op.f("ix_platform_audit_events_occurred_at"),
        table_name="platform_audit_events",
    )
    op.drop_index(
        op.f("ix_platform_audit_events_event_type"),
        table_name="platform_audit_events",
    )
    op.drop_index(
        op.f("ix_platform_audit_events_institution_id"),
        table_name="platform_audit_events",
    )
    op.drop_table("platform_audit_events")