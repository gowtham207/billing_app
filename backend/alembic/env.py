from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import create_engine, pool

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.config import settings  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.migration_url.replace("%", "%%"))
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(url=settings.migration_url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(settings.migration_url, poolclass=pool.NullPool)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        context.configure(connection=connection, target_metadata=target_metadata, transaction_per_migration=False)
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
