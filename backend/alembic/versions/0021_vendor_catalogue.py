"""Add vendor product catalogues and immutable Lock product snapshots.

Revision ID: 0021_vendor_catalogue
Revises: 0020_hot_read_indexes
"""

from alembic import op
import sqlalchemy as sa


revision = "0021_vendor_catalogue"
down_revision = "0020_hot_read_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendor_products",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("vendor_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vendor_products_vendor_id", "vendor_products", ["vendor_id"])
    op.create_index("ix_vendor_products_status", "vendor_products", ["status"])
    op.add_column("commitments", sa.Column("vendor_product_id", sa.String(), nullable=True))
    op.add_column("commitments", sa.Column("product_name_snapshot", sa.String(), nullable=True))
    op.add_column("commitments", sa.Column("product_price_snapshot", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_commitments_vendor_product_id",
        "commitments",
        "vendor_products",
        ["vendor_product_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_commitments_vendor_product_id", "commitments", type_="foreignkey")
    op.drop_column("commitments", "product_price_snapshot")
    op.drop_column("commitments", "product_name_snapshot")
    op.drop_column("commitments", "vendor_product_id")
    op.drop_index("ix_vendor_products_status", table_name="vendor_products")
    op.drop_index("ix_vendor_products_vendor_id", table_name="vendor_products")
    op.drop_table("vendor_products")
