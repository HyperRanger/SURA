"""add durable rotating Lock deadlines, member declines, and support cases

Revision ID: 0014_lock_lifecycle
Revises: 0013_contact_lookup_limit
"""

from alembic import op
import sqlalchemy as sa
from calendar import monthrange
from datetime import datetime, timedelta


revision = "0014_lock_lifecycle"
down_revision = "0013_contact_lookup_limit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("commitments", sa.Column("first_cycle_due_at", sa.DateTime(), nullable=True))
    op.add_column("commitments", sa.Column("current_cycle_due_at", sa.DateTime(), nullable=True))
    op.add_column("commitments", sa.Column("grace_period_hours", sa.Integer(), nullable=False, server_default="72"))
    op.add_column("commitments", sa.Column("missed_cycle_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("commitment_members", sa.Column("declined_at", sa.DateTime(), nullable=True))
    op.create_table(
        "commitment_cases",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("commitment_id", sa.String(), sa.ForeignKey("commitments.id"), nullable=False),
        sa.Column("bank_id", sa.String(), sa.ForeignKey("bank_partners.id"), nullable=False),
        sa.Column("opened_by", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_commitment_cases_commitment_id", "commitment_cases", ["commitment_id"])
    op.create_index("ix_commitment_cases_bank_id", "commitment_cases", ["bank_id"])

    # Legacy rows predate an explicit deadline. Give them a deterministic
    # schedule anchored to creation rather than leaving them immune to the new
    # lifecycle forever. New commitments always store their agreed deadline.
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, frequency, current_cycle_number, created_at FROM commitments")).mappings()
    for row in rows:
        # The original schema allowed a nullable creation timestamp. A small
        # number of imported legacy rows may therefore not have one. Keep the
        # migration deployable by using migration time as their deterministic
        # schedule anchor rather than failing the entire release.
        created_at = row["created_at"] or datetime.utcnow()
        due_at = created_at
        cycles_elapsed = max(0, (row["current_cycle_number"] or 1) - 1)
        for _ in range(cycles_elapsed + 1):
            if row["frequency"] == "weekly":
                due_at += timedelta(days=7)
            elif row["frequency"] == "monthly":
                month = due_at.month + 1
                year = due_at.year
                if month == 13:
                    month, year = 1, year + 1
                due_at = due_at.replace(year=year, month=month, day=min(due_at.day, monthrange(year, month)[1]))
            else:
                # Existing invalid frequencies remain readable; only the new
                # endpoint accepts weekly/monthly going forward.
                due_at += timedelta(days=7)
        bind.execute(
            sa.text("UPDATE commitments SET first_cycle_due_at = :first_due_at, current_cycle_due_at = :current_due_at WHERE id = :id"),
            {"id": row["id"], "first_due_at": _first_due_at(created_at, row["frequency"]), "current_due_at": due_at},
        )


def _first_due_at(created_at, frequency):
    if frequency == "monthly":
        month = created_at.month + 1
        year = created_at.year
        if month == 13:
            month, year = 1, year + 1
        return created_at.replace(year=year, month=month, day=min(created_at.day, monthrange(year, month)[1]))
    return created_at + timedelta(days=7)


def downgrade() -> None:
    op.drop_index("ix_commitment_cases_bank_id", table_name="commitment_cases")
    op.drop_index("ix_commitment_cases_commitment_id", table_name="commitment_cases")
    op.drop_table("commitment_cases")
    op.drop_column("commitment_members", "declined_at")
    op.drop_column("commitments", "missed_cycle_count")
    op.drop_column("commitments", "grace_period_hours")
    op.drop_column("commitments", "current_cycle_due_at")
    op.drop_column("commitments", "first_cycle_due_at")
