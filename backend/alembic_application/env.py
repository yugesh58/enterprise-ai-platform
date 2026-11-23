from logging.config import fileConfig
import os
from pathlib import Path

from alembic import context
from dotenv import dotenv_values
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL

from app.models.application_metadata import metadata
import app.models.llm_usage_event  # noqa: F401 — register application tables.


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Prefer injected environment variables (Docker/CI), with .env as fallback.
project_root = Path(config.config_file_name).resolve().parent
env_values = dotenv_values(project_root / ".env")


def get_config_value(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key) or env_values.get(key) or default


username = get_config_value("APP_MIGRATION_USER")
password = get_config_value("APP_MIGRATION_PASSWORD")

if not username or not password:
    raise RuntimeError(
        "APP_MIGRATION_USER and APP_MIGRATION_PASSWORD "
        "must be provided through environment variables or backend .env."
    )

runtime_username = get_config_value("APP_DATABASE_USER")

if not runtime_username:
    raise RuntimeError(
        "APP_DATABASE_USER must be provided through environment "
        "variables or backend .env."
    )

config.attributes["app_runtime_user"] = runtime_username

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=username,
    password=password,
    host=get_config_value("APP_DATABASE_HOST", "localhost"),
    port=int(get_config_value("APP_DATABASE_PORT", "5432")),
    database=get_config_value("APP_DATABASE_NAME", "enterprise_ai"),
)

# Escape percent signs for ConfigParser interpolation.
config.set_main_option(
    "sqlalchemy.url",
    database_url.render_as_string(hide_password=False).replace("%", "%%"),
)

target_metadata = metadata
VERSION_TABLE = "application_alembic_version"


def include_name(name, type_, parent_names):
    """Restrict this migration environment to its owned application table."""
    if type_ == "table":
        return name == "llm_usage_events"

    if type_ in {
        "column",
        "index",
        "unique_constraint",
        "foreign_key_constraint",
    }:
        return parent_names.get("table_name") == "llm_usage_events"

    return True


def run_migrations_offline() -> None:
    context.configure(
        url=database_url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        include_name=include_name,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=VERSION_TABLE,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_name=include_name,
                version_table=VERSION_TABLE,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
