import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy.dialects import postgresql


MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "alembic_application"
    / "versions"
    / "app0001_create_llm_usage_events.py"
)


@pytest.fixture
def migration(monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "app0001_create_llm_usage_events",
        MIGRATION_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    module.op.create_table = Mock()
    module.op.create_index = Mock()
    module.op.execute = Mock()
    module.op.drop_table = Mock()

    return module


def configure_runtime_role(monkeypatch, migration, role):
    context = SimpleNamespace(
        config=SimpleNamespace(
            attributes={"app_runtime_user": role}
        )
    )

    bind = SimpleNamespace(dialect=postgresql.dialect())

    monkeypatch.setattr(
        migration.op,
        "get_context",
        lambda: context,
    )
    monkeypatch.setattr(
        migration.op,
        "get_bind",
        lambda: bind,
    )


def test_upgrade_grants_access_only_to_usage_events(
    monkeypatch, migration
):
    configure_runtime_role(
        monkeypatch,
        migration,
        "app_runtime_user",
    )

    migration.upgrade()

    migration.op.create_table.assert_called_once()
    assert migration.op.create_table.call_args.args[0] == (
        "llm_usage_events"
    )

    migration.op.execute.assert_called_once_with(
        "GRANT SELECT, INSERT ON TABLE "
        "llm_usage_events TO app_runtime_user"
    )

    assert "ON TABLES" not in migration.op.execute.call_args.args[0]


def test_upgrade_quotes_runtime_role_identifier(
    monkeypatch, migration
):
    configure_runtime_role(
        monkeypatch,
        migration,
        'runtime"user',
    )

    migration.upgrade()

    migration.op.execute.assert_called_once_with(
        'GRANT SELECT, INSERT ON TABLE '
        'llm_usage_events TO "runtime""user"'
    )


def test_upgrade_fails_without_runtime_role(
    monkeypatch, migration
):
    context = SimpleNamespace(
        config=SimpleNamespace(attributes={})
    )
    monkeypatch.setattr(
        migration.op,
        "get_context",
        lambda: context,
    )

    with pytest.raises(
        RuntimeError,
        match="APP_DATABASE_USER",
    ):
        migration.upgrade()

    migration.op.create_table.assert_not_called()
    migration.op.execute.assert_not_called()


def test_downgrade_drops_only_usage_events(migration):
    migration.downgrade()

    migration.op.drop_table.assert_called_once_with(
        "llm_usage_events"
    )
