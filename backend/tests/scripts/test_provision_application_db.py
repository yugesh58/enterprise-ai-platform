import subprocess

from scripts import provision_application_db


def test_default_function_execute_is_revoked_from_public(
    tmp_path, monkeypatch
):
    backend_env = tmp_path / "backend.env"
    docker_env = tmp_path / "docker.env"

    backend_env.write_text(
        "APP_DATABASE_USER=app_runtime_user\n"
        "APP_DATABASE_PASSWORD=runtime_password_12345678901234567890\n"
        "APP_MIGRATION_USER=app_migration_user\n"
        "APP_MIGRATION_PASSWORD=migration_password_12345678901234567890\n"
        "APP_DATABASE_NAME=enterprise_ai\n"
    )
    docker_env.write_text("POSTGRES_USER=enterprise_user\n")

    monkeypatch.setattr(
        provision_application_db, "BACKEND_ENV", backend_env
    )
    monkeypatch.setattr(
        provision_application_db, "DOCKER_ENV", docker_env
    )

    captured = {}

    def fake_run(command, **kwargs):
        captured["sql"] = kwargs["input"]
        return subprocess.CompletedProcess(
            command, 0, stdout="", stderr=""
        )

    monkeypatch.setattr(
        provision_application_db.subprocess, "run", fake_run
    )

    assert provision_application_db.main() == 0

    sql = captured["sql"]

    assert sql.lstrip().startswith("BEGIN;")
    assert sql.rstrip().endswith("COMMIT;")
    assert "GRANT SELECT, INSERT ON TABLES" not in sql
    assert "GRANT SELECT, INSERT ON TABLE public.llm_usage_events" in sql

    assert "DO $check_role_memberships$" in sql
    assert "granted_role.rolname IN (" in sql
    assert "member_role.rolname IN (" in sql
    assert sql.count("NOINHERIT") == 4

    assert "DO $check_runtime_object_privileges$" in sql
    assert "runtime_role_oid" in sql
    assert "relation.relkind IN ('r', 'p', 'v', 'm', 'f')" in sql
    assert "acldefault('r', relation.relowner)" in sql
    assert "acldefault('S', sequence.relowner)" in sql
    assert "acldefault('f', routine.proowner)" in sql
    assert "privilege.grantee = 0" in sql
    assert "relation.oid IS DISTINCT FROM target_table_oid" in sql
    assert "Unexpected PUBLIC or runtime privileges on public tables" in sql
    assert "Unexpected PUBLIC or runtime privileges on public sequences" in sql
    assert "Unexpected PUBLIC or runtime privileges on public functions" in sql

    assert "DO $check_public_function_execution$" in sql
    assert "aclexplode(" in sql
    assert "acldefault('f', routine.proowner)" in sql
    assert "privilege.grantee = 0" in sql
    assert "privilege.privilege_type = 'EXECUTE'" in sql
    assert "DO $ownership_preflight$" in sql
    assert "relation.relowner = migration_role_oid" in sql
    assert "routine.proowner = migration_role_oid" in sql
    assert "namespace.nspowner = migration_role_oid" in sql
    assert "database.datdba = migration_role_oid" in sql
    assert "runtime_role_oid oid" in sql
    assert "relation.relowner = runtime_role_oid" in sql
    assert "routine.proowner = runtime_role_oid" in sql
    assert "namespace.nspowner = runtime_role_oid" in sql
    assert "database.datdba = runtime_role_oid" in sql
    assert "relation.oid IS DISTINCT FROM target_table_oid" in sql
    assert "target_version_table_oid" in sql
    assert (
        "relation.oid IS DISTINCT FROM target_version_table_oid" in sql
    )
    assert "dependency.deptype IN ('a', 'i')" in sql

    assert (
        'ALTER DEFAULT PRIVILEGES FOR ROLE "app_migration_user"\n'
        "IN SCHEMA public\n"
        'REVOKE SELECT, INSERT ON TABLES FROM "app_runtime_user";'
    ) in sql

    assert (
        'ALTER DEFAULT PRIVILEGES FOR ROLE "app_migration_user"\n'
        "REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;"
    ) in sql
