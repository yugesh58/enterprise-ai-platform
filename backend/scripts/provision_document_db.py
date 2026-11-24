"""Provision a least-privilege PostgreSQL role for document operations."""

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


def build_provisioning_sql(
    database: str,
    role: str,
    password: str,
) -> str:
    database_value = sql_literal(database)
    database_identifier = sql_identifier(database)
    role_value = sql_literal(role)
    role_identifier = sql_identifier(role)
    password_value = sql_literal(password)

    return f"""
BEGIN;

DO $preflight$
DECLARE
    role_oid oid;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables
        WHERE schemaname = 'public' AND tablename = 'documents'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_tables
        WHERE schemaname = 'public' AND tablename = 'document_chunks'
    ) THEN
        RAISE EXCEPTION 'Required document tables are missing.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename IN ('documents', 'document_chunks')
          AND tableowner <> current_user
    ) THEN
        RAISE EXCEPTION
            'Document table ownership differs from the provisioning administrator.';
    END IF;

    SELECT oid INTO role_oid
    FROM pg_roles
    WHERE rolname = {role_value};

    IF role_oid IS NOT NULL THEN
        IF EXISTS (
            SELECT 1
            FROM pg_auth_members
            WHERE roleid = role_oid OR member = role_oid
        ) THEN
            RAISE EXCEPTION
                'Document runtime role has role memberships; manual review required.';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM pg_class relation
            JOIN pg_namespace namespace
              ON namespace.oid = relation.relnamespace
            WHERE relation.relowner = role_oid
              AND namespace.nspname NOT IN (
                  'pg_catalog', 'information_schema'
              )
        ) OR EXISTS (
            SELECT 1 FROM pg_namespace
            WHERE nspowner = role_oid
              AND nspname NOT IN ('pg_catalog', 'information_schema')
        ) OR EXISTS (
            SELECT 1 FROM pg_proc
            WHERE proowner = role_oid
              AND pronamespace NOT IN (
                  SELECT oid FROM pg_namespace
                  WHERE nspname IN ('pg_catalog', 'information_schema')
              )
        ) OR EXISTS (
            SELECT 1 FROM pg_database WHERE datdba = role_oid
        ) THEN
            RAISE EXCEPTION
                'Document runtime role owns database objects; manual review required.';
        END IF;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_database database
        CROSS JOIN LATERAL aclexplode(
            COALESCE(
                database.datacl,
                acldefault('d', database.datdba)
            )
        ) privilege
        WHERE database.datname = {database_value}
          AND privilege.grantee = 0
          AND privilege.privilege_type IN ('CREATE', 'TEMPORARY')
    ) THEN
        RAISE EXCEPTION
            'PUBLIC has database CREATE or TEMPORARY privileges; manual review required.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_namespace namespace
        CROSS JOIN LATERAL aclexplode(
            COALESCE(
                namespace.nspacl,
                acldefault('n', namespace.nspowner)
            )
        ) privilege
        WHERE namespace.nspname = 'public'
          AND privilege.grantee = 0
          AND privilege.privilege_type = 'CREATE'
    ) THEN
        RAISE EXCEPTION
            'PUBLIC has CREATE on public schema; manual review required.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_class relation
        JOIN pg_namespace namespace
          ON namespace.oid = relation.relnamespace
        CROSS JOIN LATERAL aclexplode(
            COALESCE(
                relation.relacl,
                acldefault(
                    CASE WHEN relation.relkind = 'S' THEN 'S'::"char" ELSE 'r'::"char" END,
                    relation.relowner
                )
            )
        ) privilege
        WHERE namespace.nspname = 'public'
          AND relation.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')
          AND privilege.grantee = 0
    ) THEN
        RAISE EXCEPTION
            'PUBLIC has privileges on public tables or sequences; manual review required.';
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
          AND privilege.grantee = 0
          AND privilege.privilege_type = 'EXECUTE'
    ) THEN
        RAISE EXCEPTION
            'PUBLIC has EXECUTE on public functions; manual review required.';
    END IF;
END
$preflight$;

DO $provision_role$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = {role_value}
    ) THEN
        EXECUTE format(
            'CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB '
            'NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
            {role_value},
            {password_value}
        );
    ELSE
        EXECUTE format(
            'ALTER ROLE %I WITH LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB '
            'NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
            {role_value},
            {password_value}
        );
    END IF;
END
$provision_role$;

REVOKE ALL PRIVILEGES ON DATABASE {database_identifier}
    FROM {role_identifier};
GRANT CONNECT ON DATABASE {database_identifier} TO {role_identifier};

REVOKE ALL PRIVILEGES ON SCHEMA public FROM {role_identifier};
GRANT USAGE ON SCHEMA public TO {role_identifier};

REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public
    FROM {role_identifier};
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public
    FROM {role_identifier};
REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public
    FROM {role_identifier};

GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE public.documents TO {role_identifier};

GRANT SELECT, INSERT, DELETE
    ON TABLE public.document_chunks TO {role_identifier};

ALTER ROLE {role_identifier} IN DATABASE {database_identifier}
    SET search_path = 'pg_catalog, public';

DO $verify_permissions$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_roles
        WHERE rolname = {role_value}
          AND (
              rolsuper OR rolcreatedb OR rolcreaterole
              OR rolreplication OR rolbypassrls OR rolinherit
          )
    ) THEN
        RAISE EXCEPTION 'Document runtime role attributes are too permissive.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_auth_members
        WHERE roleid = (SELECT oid FROM pg_roles WHERE rolname = {role_value})
           OR member = (SELECT oid FROM pg_roles WHERE rolname = {role_value})
    ) THEN
        RAISE EXCEPTION 'Document runtime role has role memberships.';
    END IF;

    IF has_database_privilege({role_value}, {database_value}, 'CREATE')
       OR has_database_privilege({role_value}, {database_value}, 'TEMPORARY')
       OR NOT has_database_privilege({role_value}, {database_value}, 'CONNECT')
    THEN
        RAISE EXCEPTION 'Unexpected document database privileges.';
    END IF;

    IF has_schema_privilege({role_value}, 'public', 'CREATE')
       OR NOT has_schema_privilege({role_value}, 'public', 'USAGE')
    THEN
        RAISE EXCEPTION 'Unexpected public schema privileges.';
    END IF;

    IF NOT (
        has_table_privilege({role_value}, 'public.documents', 'SELECT')
        AND has_table_privilege({role_value}, 'public.documents', 'INSERT')
        AND has_table_privilege({role_value}, 'public.documents', 'UPDATE')
        AND has_table_privilege({role_value}, 'public.documents', 'DELETE')
        AND has_table_privilege({role_value}, 'public.document_chunks', 'SELECT')
        AND has_table_privilege({role_value}, 'public.document_chunks', 'INSERT')
        AND has_table_privilege({role_value}, 'public.document_chunks', 'DELETE')
    ) THEN
        RAISE EXCEPTION 'Required document table privileges are missing.';
    END IF;

    IF has_table_privilege(
        {role_value}, 'public.document_chunks', 'UPDATE'
    ) OR has_table_privilege(
        {role_value}, 'public.employee', 'SELECT'
    ) OR has_table_privilege(
        {role_value}, 'public.alembic_version', 'SELECT'
    ) THEN
        RAISE EXCEPTION 'Document runtime role has excessive table privileges.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_namespace namespace
        WHERE namespace.nspname NOT IN (
            'pg_catalog', 'information_schema', 'public'
        )
          AND (
              has_schema_privilege({role_value}, namespace.oid, 'USAGE')
              OR has_schema_privilege({role_value}, namespace.oid, 'CREATE')
          )
    ) THEN
        RAISE EXCEPTION 'Document runtime role has access to an unapproved schema.';
    END IF;
END
$verify_permissions$;

COMMIT;
"""


def main() -> int:
    if not BACKEND_ENV.is_file() or not DOCKER_ENV.is_file():
        print("Required backend/.env or docker/.env file is missing.")
        return 1

    app = dotenv_values(BACKEND_ENV)
    docker = dotenv_values(DOCKER_ENV)

    database = app.get("DOCUMENT_DATABASE_NAME")
    runtime_user = app.get("DOCUMENT_DATABASE_USER")
    runtime_password = app.get("DOCUMENT_DATABASE_PASSWORD")
    admin_user = docker.get("POSTGRES_USER") or "enterprise_user"

    if not all(isinstance(value, str) and value for value in (
        database, runtime_user, runtime_password, admin_user
    )):
        print("Document database credentials or database name are missing.")
        return 1

    if runtime_user == admin_user or runtime_user in {
        "app_runtime_user",
        "app_migration_user",
        "sql_agent_user",
    }:
        print("Document runtime role name must be unique.")
        return 1

    if len(runtime_password) < 32:
        print("Document runtime password must contain at least 32 characters.")
        return 1

    sql = build_provisioning_sql(
        database=database,
        role=runtime_user,
        password=runtime_password,
    )

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
        print("Document database provisioning failed.")
        if result.stderr:
            print(result.stderr)
        return result.returncode

    print("Document runtime role provisioned successfully.")
    print("Documents: SELECT, INSERT, UPDATE, DELETE.")
    print("Document chunks: SELECT, INSERT, DELETE.")
    print("Employee and migration tables: no access.")
    print("Passwords were not displayed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
