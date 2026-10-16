from logging.config import fileConfig

from alembic import context
from app.core.config import settings
from app.core.database import build_engine
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=settings.db_schema,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Mismo engine que la app (URL de .env y search_path = esquema_a), para no duplicar
    # credenciales en alembic.ini y que las migraciones solo toquen esquema_a.
    connectable = build_engine(settings.database_url, settings.db_schema)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # La tabla alembic_version también vive en esquema_a
            version_table_schema=settings.db_schema,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
