"""Provision a least-privilege PostgreSQL role for the SQL Agent."""

from pathlib import Path
import subprocess

from dotenv import dotenv_values

from app.storage.database.sql_agent_policy import APPROVED_SQL_AGENT_TABLES


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
    role_value = sql_literal(role)
    password_value = sql_literal(password)
    role_identifier = sql_identifier(role)
    database_identifier = sql_identifier(database)
    database_value = sql_literal(database)
    table_identifiers = ",\n    ".join(
        f'{sql_identifier("public")}.{sql_identifier(table)}'
        for table in sorted(APPROVED_SQL_AGENT_TABLES)
    )
    table_names = ", ".join(
        sql_literal(table)
        for table in sorted(APPROVED_SQL_AGENT_TABLES)
    )

    return f"""
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
        WHERE granted_role.rolname = {role_value}
           OR member_role.rolname = {role_value}
    ) THEN
        RAISE EXCEPTION
            'SQL Agent role has existing memberships; manual review is required.';
    END IF;
END
$check_role_memberships$;

DO $check_public_privileges$
BEGIN
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
            'PUBLIC has database CREATE or TEMPORARY privileges; manual review is required.';
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
        WHERE namespace.nspname NOT IN (
            'pg_catalog', 'information_schema'
        )
          AND namespace.nspname NOT LIKE 'pg_toast%'
          AND privilege.grantee = 0
          AND privilege.privilege_type = 'CREATE'
    ) THEN
        RAISE EXCEPTION
            'PUBLIC has CREATE privileges on an application schema; manual review is required.';
    END IF;
END
$check_public_privileges$;

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

DO $check_sample_tables$
DECLARE
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[{table_names}] LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM pg_class relation
            JOIN pg_namespace namespace
              ON namespace.oid = relation.relnamespace
            WHERE namespace.nspname = 'public'
              AND relation.relname = table_name
              AND relation.relkind IN ('r', 'p')
        ) THEN
            RAISE EXCEPTION
                'An approved SQL Agent sample table is missing or is not a table.';
        END IF;
    END LOOP;
END
$check_sample_tables$;

GRANT SELECT ON TABLE
    {table_identifiers}
    TO {role_identifier};

ALTER ROLE {role_identifier} IN DATABASE {database_identifier}
    SET search_path = 'pg_catalog, public';
ALTER ROLE {role_identifier} IN DATABASE {database_identifier}
    SET default_transaction_read_only = on;

DO $verify_permissions$
DECLARE
    role_oid oid;
BEGIN
    SELECT oid INTO role_oid
    FROM pg_roles
    WHERE rolname = {role_value};

    IF EXISTS (
        SELECT 1 FROM pg_roles
        WHERE oid = role_oid
          AND (
              rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication
              OR rolbypassrls OR rolinherit
          )
    ) THEN
        RAISE EXCEPTION 'SQL Agent role attributes are too permissive.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_auth_members WHERE member = role_oid
    ) THEN
        RAISE EXCEPTION 'SQL Agent role still has role memberships.';
    END IF;

    IF has_database_privilege(
        {role_value}, {database_value}, 'CREATE'
    ) OR has_database_privilege(
        {role_value}, {database_value}, 'TEMPORARY'
    ) THEN
        RAISE EXCEPTION
            'SQL Agent role has database CREATE or TEMPORARY privilege.';
    END IF;

    IF has_schema_privilege({role_value}, 'public', 'CREATE') THEN
        RAISE EXCEPTION 'SQL Agent role can create in the public schema.';
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
        RAISE EXCEPTION
            'SQL Agent role has CREATE or USAGE on an unapproved schema.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_class relation
        JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
        WHERE namespace.nspname NOT IN ('pg_catalog', 'information_schema')
          AND relation.relowner = role_oid
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
        SELECT 1 FROM pg_database
        WHERE datname = current_database() AND datdba = role_oid
    ) THEN
        RAISE EXCEPTION 'SQL Agent role must not own database objects.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_class relation
        JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
        WHERE namespace.nspname NOT IN ('pg_catalog', 'information_schema')
          AND relation.relkind IN ('r', 'p', 'v', 'm', 'f')
          AND (
              (
                  namespace.nspname = 'public'
                  AND relation.relname = ANY (ARRAY[{table_names}])
                  AND (
                      NOT has_table_privilege(
                          {role_value}, relation.oid, 'SELECT'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'INSERT'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'UPDATE'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'DELETE'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'TRUNCATE'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'REFERENCES'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'TRIGGER'
                      )
                      OR has_any_column_privilege(
                          {role_value}, relation.oid, 'INSERT'
                      )
                      OR has_any_column_privilege(
                          {role_value}, relation.oid, 'UPDATE'
                      )
                      OR has_any_column_privilege(
                          {role_value}, relation.oid, 'REFERENCES'
                      )
                  )
              )
              OR (
                  NOT (
                      namespace.nspname = 'public'
                      AND relation.relname = ANY (ARRAY[{table_names}])
                  )
                  AND (
                      has_table_privilege(
                          {role_value}, relation.oid, 'SELECT'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'INSERT'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'UPDATE'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'DELETE'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'TRUNCATE'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'REFERENCES'
                      )
                      OR has_table_privilege(
                          {role_value}, relation.oid, 'TRIGGER'
                      )
                      OR has_any_column_privilege(
                          {role_value}, relation.oid, 'SELECT'
                      )
                      OR has_any_column_privilege(
                          {role_value}, relation.oid, 'INSERT'
                      )
                      OR has_any_column_privilege(
                          {role_value}, relation.oid, 'UPDATE'
                      )
                      OR has_any_column_privilege(
                          {role_value}, relation.oid, 'REFERENCES'
                      )
                  )
              )
          )
    ) THEN
        RAISE EXCEPTION
            'SQL Agent role has privileges outside approved sample tables.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_proc routine
        JOIN pg_namespace namespace
          ON namespace.oid = routine.pronamespace
        WHERE namespace.nspname = 'public'
          AND has_function_privilege(
              {role_value}, routine.oid, 'EXECUTE'
          )
    ) THEN
        RAISE EXCEPTION
            'SQL Agent role has EXECUTE privileges on public functions.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_class sequence
        JOIN pg_namespace namespace ON namespace.oid = sequence.relnamespace
        WHERE namespace.nspname NOT IN ('pg_catalog', 'information_schema')
          AND sequence.relkind = 'S'
          AND (
              has_sequence_privilege(
                  {role_value}, sequence.oid, 'USAGE'
              )
              OR has_sequence_privilege(
                  {role_value}, sequence.oid, 'SELECT'
              )
              OR has_sequence_privilege(
                  {role_value}, sequence.oid, 'UPDATE'
              )
          )
    ) THEN
        RAISE EXCEPTION 'SQL Agent role has sequence privileges.';
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

    environment = (app.get("ENVIRONMENT") or "development").lower()
    role = app.get("SQL_AGENT_DATABASE_USER")
    password = app.get("SQL_AGENT_DATABASE_PASSWORD")
    used_development_fallback = False

    # Match SQL_AGENT_DATABASE_URL fallback behaviour in config.py.
    if (
        environment == "development"
        and not role
        and not password
    ):
        role = app.get("DATABASE_USER")
        password = app.get("DATABASE_PASSWORD")
        used_development_fallback = True

    database = app.get("DATABASE_NAME") or "enterprise_ai"
    admin_user = docker.get("POSTGRES_USER") or "enterprise_user"

    other_users = {
        app.get("APP_DATABASE_USER"),
        app.get("APP_MIGRATION_USER"),
        app.get("DOCUMENT_DATABASE_USER"),
        admin_user,
    }

    # DATABASE_USER is a separate identity unless it is the intentional
    # development fallback used by the SQL Agent.
    database_user = app.get("DATABASE_USER")
    if database_user and not used_development_fallback:
        other_users.add(database_user)

    if not all(
        isinstance(value, str) and value
        for value in (role, password, database, admin_user)
    ):
        print("SQL Agent credentials and database settings are required.")
        return 1

    if role in other_users:
        print(
            "SQL Agent must use a distinct role from application, "
            "migration, document, and administrator roles."
        )
        return 1

    if len(password) < 32:
        print("SQL_AGENT_DATABASE_PASSWORD must contain at least 32 characters.")
        return 1

    sql = build_provisioning_sql(database, role, password)
    command = [
        "docker",
        "exec",
        "-i",
        CONTAINER,
        "psql",
        "-U",
        admin_user,
        "-d",
        database,
        "-v",
        "ON_ERROR_STOP=1",
    ]

    try:
        result = subprocess.run(
            command,
            input=sql,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        print("Could not run Docker to provision the SQL Agent role.")
        return 1

    if result.returncode:
        print(
            "SQL Agent role provisioning failed; "
            "database output was suppressed."
        )
        return result.returncode

    print(
        "SQL Agent role provisioned with SELECT-only access "
        "to approved sample tables."
    )
    print("No table data or schema objects were modified.")
    print("Database ACLs were tightened; credentials were not displayed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
