"""W16 tenant consistency database invariants.

Revision ID: w16_tenant_db_invariants
Revises: w16_skill_marketplace
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "w16_tenant_db_invariants"
down_revision = "w16_skill_marketplace"
branch_labels = None
depends_on = None


def upgrade():
    # Composite references require matching tenant_id + entity id at the
    # database boundary. Existing single-column FKs are replaced below.
    op.create_unique_constraint(
        "uq_employees_tenant_id_id",
        "employees",
        ["tenant_id", "id"],
    )
    op.create_unique_constraint(
        "uq_products_tenant_id_id",
        "products",
        ["tenant_id", "id"],
    )
    op.create_unique_constraint(
        "uq_skill_packages_tenant_id_id",
        "skill_packages",
        ["tenant_id", "id"],
    )

    op.drop_constraint(
        "employee_skill_installations_tenant_id_fkey",
        "employee_skill_installations",
        type_="foreignkey",
    )
    op.drop_constraint(
        "employee_skill_installations_employee_id_fkey",
        "employee_skill_installations",
        type_="foreignkey",
    )
    op.drop_constraint(
        "employee_skill_installations_skill_package_id_fkey",
        "employee_skill_installations",
        type_="foreignkey",
    )
    op.drop_constraint(
        "skill_packages_tenant_id_fkey",
        "skill_packages",
        type_="foreignkey",
    )
    op.drop_constraint(
        "skill_packages_product_id_fkey",
        "skill_packages",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "fk_skill_packages_tenant",
        "skill_packages",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_skill_packages_product_tenant",
        "skill_packages",
        "products",
        ["tenant_id", "product_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )

    op.create_foreign_key(
        "fk_employee_skill_installations_tenant",
        "employee_skill_installations",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_employee_skill_installations_employee_tenant",
        "employee_skill_installations",
        "employees",
        ["tenant_id", "employee_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_employee_skill_installations_skill_package_tenant",
        "employee_skill_installations",
        "skill_packages",
        ["tenant_id", "skill_package_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        "fk_employee_skill_installations_skill_package_tenant",
        "employee_skill_installations",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_employee_skill_installations_employee_tenant",
        "employee_skill_installations",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_employee_skill_installations_tenant",
        "employee_skill_installations",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_skill_packages_product_tenant",
        "skill_packages",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_skill_packages_tenant",
        "skill_packages",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "skill_packages_tenant_id_fkey",
        "skill_packages",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "skill_packages_product_id_fkey",
        "skill_packages",
        "products",
        ["product_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "employee_skill_installations_tenant_id_fkey",
        "employee_skill_installations",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "employee_skill_installations_employee_id_fkey",
        "employee_skill_installations",
        "employees",
        ["employee_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "employee_skill_installations_skill_package_id_fkey",
        "employee_skill_installations",
        "skill_packages",
        ["skill_package_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("uq_skill_packages_tenant_id_id", "skill_packages", type_="unique")
    op.drop_constraint("uq_products_tenant_id_id", "products", type_="unique")
    op.drop_constraint("uq_employees_tenant_id_id", "employees", type_="unique")
