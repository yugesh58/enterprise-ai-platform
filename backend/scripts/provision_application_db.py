"""Provision restricted PostgreSQL application roles and privileges."""

from pathlib import Path

import subprocess

from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ENV = ROOT / ".env"
DOCKER_ENV = ROOT.parent / "docker" / ".env"
CONTAINER = "enterprise-ai-postgres"


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def main() -> int:
    if not BACKEND_ENV.is_file() or not DOCKER_ENV.is_file():
        print("Required backend/.env or docker/.env file is missing.")
        return 1

    app = dotenv_values(BACKEND_ENV)
    docker = dotenv_values(DOCKER_ENV)

    runtime_user = app.get("APP_DATABASE_USER")
    runtime_password = app.get("APP_DATABASE_PASSWORD")
    migration_user = app.get("APP_MIGRATION_USER")
    migration_password = app.get("APP_MIGRATION_PASSWORD")

    database = app.get("APP_DATABASE_NAME") or "enterprise_ai"
    admin_user = docker.get("POSTGRES_USER") or "enterprise_user"

    if not all(isinstance(value, str) and value for value in (
        database, admin_user, runtime_user, migration_user
    )):
        print("Database and role names must be non-empty strings.")
        return 1

    credentials = (
        runtime_user,
        runtime_password,
        migration_user,
        migration_password,
    )

    if not all(credentials):
        print("Application runtime or migration credentials are missing.")
        return 1

    if runtime_user == migration_user or admin_user in {
        runtime_user,
        migration_user,
    }:
        print("Database role names must be distinct.")
        return 1

    if len(runtime_password) < 32 or len(migration_password) < 32:
        print("Application role passwords must contain at least 32 characters.")
        return 1

    sql = f"""
BEGIN;

DO $check_role_memberships$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_auth_members membership
        JOIN pg_roles granted_role
          ON granted_role.oid = membership.roleid
        JOIN pg_roles member_role
          ON member_role.oid = membership.member
        WHERE granted_role.rolname IN (
            {sql_literal(runtime_user)},
            {sql_literal(migration_user)}
        )
        OR member_role.rolname IN (
            {sql_literal(runtime_user)},
            {sql_literal(migration_user)}
        )
    ) THEN
        RAISE EXCEPTION
            'Application roles have existing memberships; manual review is required.';
    END IF;
END
$check_role_memberships$;

DO $check_public_function_execution$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_proc routine
        JOIN pg_namespace namespace
          ON namespace.oid = routine.pronamespace
        CROSS JOIN LATERAL aclexplode(
            COALESCE(
                routine.proacl,
                acldefault('f', routine.proowner)
            )
        ) privilege
        WHERE namespace.nspname = 'public'
          AND privilege.grantee = 0
          AND privilege.privilege_type = 'EXECUTE'
    ) THEN
        RAISE EXCEPTION
            'PUBLIC has EXECUTE privileges on public functions; manual review is required.';
    END IF;
END
$check_public_function_execution$;

DO $ownership_preflight$
DECLARE
    migration_role_oid oid;
    runtime_role_oid oid;
    target_table_oid oid := to_regclass('public.llm_usage_events');
    target_version_table_oid oid :=
        to_regclass('public.application_alembic_version');
BEGIN
    SELECT oid INTO migration_role_oid
    FROM pg_roles
    WHERE rolname = {sql_literal(migration_user)};

    SELECT oid INTO runtime_role_oid
    FROM pg_roles
    WHERE rolname = {sql_literal(runtime_user)};

    IF migration_role_oid IS NOT NULL THEN

        IF EXISTS (
            SELECT 1
            FROM pg_class relation
            JOIN pg_namespace namespace
              ON namespace.oid = relation.relnamespace
            WHERE relation.relowner = migration_role_oid
              AND relation.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')
              AND namespace.nspname NOT IN (
                  'pg_catalog', 'information_schema'
              )
              AND namespace.nspname NOT LIKE 'pg_toast%'
              AND relation.oid IS DISTINCT FROM target_table_oid
              AND relation.oid IS DISTINCT FROM target_version_table_oid
              AND NOT (
                  relation.relkind = 'S'
                  AND target_table_oid IS NOT NULL
                  AND EXISTS (
                      SELECT 1
                      FROM pg_depend dependency
                      WHERE dependency.classid = 'pg_class'::regclass
                        AND dependency.objid = relation.oid
                        AND dependency.refclassid = 'pg_class'::regclass
                        AND dependency.refobjid = target_table_oid
                        AND dependency.deptype IN ('a', 'i')
                  )
              )
        ) THEN
            RAISE EXCEPTION
                'Unexpected relations owned by application migration role.';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM pg_proc routine
            JOIN pg_namespace namespace
              ON namespace.oid = routine.pronamespace
            WHERE routine.proowner = migration_role_oid
              AND namespace.nspname NOT IN (
                  'pg_catalog', 'information_schema'
              )
              AND namespace.nspname NOT LIKE 'pg_toast%'
        ) THEN
            RAISE EXCEPTION
                'Functions owned by application migration role.';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM pg_namespace namespace
            WHERE namespace.nspowner = migration_role_oid
              AND namespace.nspname NOT IN (
                  'pg_catalog', 'information_schema'
              )
              AND namespace.nspname NOT LIKE 'pg_toast%'
        ) THEN
            RAISE EXCEPTION
                'Schemas owned by application migration role.';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM pg_database database
            WHERE database.datdba = migration_role_oid
        ) THEN
            RAISE EXCEPTION
                'Database owned by application migration role.';
        END IF;
    END IF;
    IF runtime_role_oid IS NOT NULL THEN
        IF EXISTS (
            SELECT 1
            FROM pg_class relation
            JOIN pg_namespace namespace
              ON namespace.oid = relation.relnamespace
            WHERE relation.relowner = runtime_role_oid
              AND relation.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')
              AND namespace.nspname NOT IN (
                  'pg_catalog', 'information_schema'
              )
              AND namespace.nspname NOT LIKE 'pg_toast%'
        ) THEN
            RAISE EXCEPTION
                'Unexpected relations owned by application runtime role.';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM pg_proc routine
            JOIN pg_namespace namespace
              ON namespace.oid = routine.pronamespace
            WHERE routine.proowner = runtime_role_oid
              AND namespace.nspname NOT IN (
                  'pg_catalog', 'information_schema'
              )
              AND namespace.nspname NOT LIKE 'pg_toast%'
        ) THEN
            RAISE EXCEPTION
                'Functions owned by application runtime role.';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM pg_namespace namespace
            WHERE namespace.nspowner = runtime_role_oid
              AND namespace.nspname NOT IN (
                  'pg_catalog', 'information_schema'
              )
              AND namespace.nspname NOT LIKE 'pg_toast%'
        ) THEN
            RAISE EXCEPTION
                'Schemas owned by application runtime role.';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM pg_database database
            WHERE database.datdba = runtime_role_oid
        ) THEN
            RAISE EXCEPTION
                'Database owned by application runtime role.';
        END IF;
    END IF;
END
$ownership_preflight$;

DO $check_runtime_object_privileges$
DECLARE
    runtime_role_oid oid;
    target_table_oid oid := to_regclass('public.llm_usage_events');
BEGIN
    SELECT oid INTO runtime_role_oid
    FROM pg_roles
    WHERE rolname = {sql_literal(runtime_user)};

    IF EXISTS (
        SELECT 1
        FROM pg_class relation
        JOIN pg_namespace namespace
          ON namespace.oid = relation.relnamespace
        CROSS JOIN LATERAL aclexplode(
            COALESCE(
                relation.relacl,
                acldefault('r', relation.relowner)
            )
        ) privilege
        WHERE namespace.nspname = 'public'
          AND relation.relkind IN ('r', 'p', 'v', 'm', 'f')
          AND (
              privilege.grantee = 0
              OR (
                  runtime_role_oid IS NOT NULL
                  AND privilege.grantee = runtime_role_oid
                  AND relation.oid IS DISTINCT FROM target_table_oid
              )
          )
    ) THEN
        RAISE EXCEPTION
            'Unexpected PUBLIC or runtime privileges on public tables; manual review is required.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_class sequence
        JOIN pg_namespace namespace
          ON namespace.oid = sequence.relnamespace
        CROSS JOIN LATERAL aclexplode(
            COALESCE(
                sequence.relacl,
                acldefault('S', sequence.relowner)
            )
        ) privilege
        WHERE namespace.nspname = 'public'
          AND sequence.relkind = 'S'
          AND (
              privilege.grantee = 0
              OR (
                  runtime_role_oid IS NOT NULL
                  AND privilege.grantee = runtime_role_oid
              )
          )
    ) THEN
        RAISE EXCEPTION
            'Unexpected PUBLIC or runtime privileges on public sequences; manual review is required.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_proc routine
        JOIN pg_namespace namespace
          ON namespace.oid = routine.pronamespace
        CROSS JOIN LATERAL aclexplode(
            COALESCE(
                routine.proacl,
                acldefault('f', routine.proowner)
            )
        ) privilege
        WHERE namespace.nspname = 'public'
          AND (
              privilege.grantee = 0
              OR (
                  runtime_role_oid IS NOT NULL
                  AND privilege.grantee = runtime_role_oid
              )
          )
    ) THEN
        RAISE EXCEPTION
            'Unexpected PUBLIC or runtime privileges on public functions; manual review is required.';
    END IF;
END
$check_runtime_object_privileges$;

DO $provision$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = {sql_literal(runtime_user)}
    ) THEN
        EXECUTE format(
            'CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB '
            'NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
            {sql_literal(runtime_user)},
            {sql_literal(runtime_password)}
        );
    ELSE
        EXECUTE format(
            'ALTER ROLE %I WITH LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB '
            'NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
            {sql_literal(runtime_user)},
            {sql_literal(runtime_password)}
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = {sql_literal(migration_user)}
    ) THEN
        EXECUTE format(
            'CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB '
            'NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
            {sql_literal(migration_user)},
            {sql_literal(migration_password)}
        );
    ELSE
        EXECUTE format(
            'ALTER ROLE %I WITH LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB '
            'NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
            {sql_literal(migration_user)},
            {sql_literal(migration_password)}
        );
    END IF;
END
$provision$;

GRANT CONNECT ON DATABASE {sql_identifier(database)} TO {sql_identifier(runtime_user)};
GRANT CONNECT ON DATABASE {sql_identifier(database)} TO {sql_identifier(migration_user)};

GRANT USAGE ON SCHEMA public TO {sql_identifier(runtime_user)};
GRANT USAGE, CREATE ON SCHEMA public TO {sql_identifier(migration_user)};
REVOKE CREATE ON SCHEMA public FROM {sql_identifier(runtime_user)};

ALTER DEFAULT PRIVILEGES FOR ROLE {sql_identifier(migration_user)}
IN SCHEMA public
REVOKE SELECT, INSERT ON TABLES FROM {sql_identifier(runtime_user)};

ALTER DEFAULT PRIVILEGES FOR ROLE {sql_identifier(migration_user)}
REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

DO $permissions$
BEGIN
    IF to_regclass('public.llm_usage_events') IS NOT NULL THEN
        EXECUTE format(
            'ALTER TABLE public.llm_usage_events OWNER TO %I',
            {sql_literal(migration_user)}
        );

        EXECUTE format(
            'REVOKE ALL PRIVILEGES ON TABLE public.llm_usage_events FROM %I',
            {sql_literal(runtime_user)}
        );

        EXECUTE format(
            'GRANT SELECT, INSERT ON TABLE public.llm_usage_events TO %I',
            {sql_literal(runtime_user)}
        );

        IF EXISTS (
            SELECT 1 FROM pg_roles WHERE rolname = 'sql_agent_user'
        ) THEN
            EXECUTE
                'REVOKE ALL PRIVILEGES ON TABLE public.llm_usage_events '
                'FROM sql_agent_user';
        END IF;
    END IF;
END
$permissions$;

COMMIT;
"""

    command = [
        "docker", "exec", "-i", CONTAINER,
        "psql",
        "-U", admin_user,
        "-d", database,
        "-v", "ON_ERROR_STOP=1",
    ]

    result = subprocess.run(
        command,
        input=sql,
        text=True,
        capture_output=True,
    )

    if result.returncode:
        print("Application database provisioning failed.")
        if result.stderr:
            print(result.stderr)
        return result.returncode

    print("Application database roles provisioned.")
    print("Runtime role: SELECT and INSERT on usage events only.")
    print("Migration role: schema CREATE and application table ownership.")
    print("Business tables were not modified.")
    print("Passwords were not displayed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
