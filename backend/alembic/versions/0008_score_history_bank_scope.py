"""persist bank ownership on score history

Revision ID: 0008_score_history_bank_scope
Revises: 0007_bank_portal_monitoring
"""

import sqlalchemy as sa

from alembic import op

revision = "0008_score_history_bank_scope"
down_revision = "0007_bank_portal_monitoring"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("score_history", sa.Column("bank_id", sa.String(), nullable=True))
    op.execute(
        "UPDATE score_history AS score "
        "SET bank_id = users.bank_id "
        "FROM users WHERE score.user_id = users.id"
    )
    # SQLite cannot add a foreign key or an index with ALTER TABLE; both must
    # recreate the table. batch_alter_table does that on SQLite and emits the
    # plain statements on PostgreSQL, so the resulting schema is identical.
    with op.batch_alter_table("score_history") as batch:
        batch.create_foreign_key(
            "fk_score_history_bank_id",
            "bank_partners",
            ["bank_id"],
            ["id"],
        )
        batch.create_index("ix_score_history_bank_id", ["bank_id"])


def downgrade() -> None:
    op.drop_index("ix_score_history_bank_id", table_name="score_history")
    op.drop_constraint("fk_score_history_bank_id", "score_history", type_="foreignkey")
    op.drop_column("score_history", "bank_id")
