"""
Environnement Alembic pour CloudDiagnoze.

Construit l'URL SQLAlchemy depuis les mêmes variables d'environnement que
api/database/connection.py et expose Base.metadata pour l'autogeneration.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Importe la Base ORM et tous les modèles pour que metadata soit complet.
from api.database.connection import Base, DATABASE_URL
from api.database import models  # noqa: F401  (import pour enregistrer les tables)

config = context.config

# Injecte l'URL construite à partir des variables d'environnement.
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Exécute les migrations en mode 'offline' (génère du SQL sans connexion)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécute les migrations en mode 'online' avec une connexion réelle."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

