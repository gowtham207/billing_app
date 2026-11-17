"""Initial CRM, billing, and inventory schema."""

from alembic import op

from app.db.schema_loader import apply_initial_schema

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    apply_initial_schema(op.get_bind())


def downgrade() -> None:
    bind = op.get_bind()
    bind.exec_driver_sql("DROP SCHEMA IF EXISTS app CASCADE")
    exists = bind.exec_driver_sql("SELECT 1 FROM pg_roles WHERE rolname = 'billing_app'").first()
    if exists is not None:
        bind.exec_driver_sql("DROP OWNED BY billing_app CASCADE")
        bind.exec_driver_sql("DROP ROLE billing_app")
