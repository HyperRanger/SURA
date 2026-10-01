"""merge the auth and bank-scope branches

0008_auth_challenges and 0008_score_history_bank_scope were both written against
0007_bank_portal_monitoring, so the tree had two heads and `alembic upgrade head`
refused to run at all. This revision only joins the two branches; there is
nothing to undo because neither parent changed anything here.

Revision ID: 0009_merge_auth_and_bank_scope
Revises: 0008_auth_challenges, 0008_score_history_bank_scope
"""



revision = "0009_merge_auth_and_bank_scope"
down_revision = ("0008_auth_challenges", "0008_score_history_bank_scope")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
