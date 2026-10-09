"""Seed the fixed Sura partner-bank catalogue used by the member app.

Revision ID: 0025_supported_partner_banks
Revises: 0024_goal_commitments
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "0025_supported_partner_banks"
down_revision = "0024_goal_commitments"
branch_labels = None
depends_on = None


PARTNER_BANKS = (
    ("bnk_sura_access", "Access Bank"),
    ("bnk_sura_gtbank", "GTBank"),
    ("bnk_sura_zenith", "Zenith Bank"),
    ("bnk_sura_firstbank", "FirstBank"),
)


def upgrade() -> None:
    now = datetime.utcnow()
    for bank_id, name in PARTNER_BANKS:
        op.execute(
            sa.text(
                """
                INSERT INTO bank_partners (
                    id, name, environment, supported_vendor_categories_json,
                    retention_days, security_settings_json, created_at, updated_at
                ) VALUES (
                    :id, :name, 'sandbox', '[]', 365, '{}', :created_at, :updated_at
                ) ON CONFLICT (id) DO NOTHING
                """
            ).bindparams(id=bank_id, name=name, created_at=now, updated_at=now)
        )


def downgrade() -> None:
    # A seeded partner can be referenced by linked accounts, users, bank staff,
    # API keys, or audit records. Do not destroy those relationships as a side
    # effect of a schema downgrade.
    pass
