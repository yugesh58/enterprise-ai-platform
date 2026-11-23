from scripts.provision_sql_agent_db import build_provisioning_sql


def test_provisioning_grants_select_only_on_explicit_sample_tables():
    sql = build_provisioning_sql(
        database="sample_db",
        role="sql_agent_test_role",
        password="test-only-not-a-real-credential",
    )

    assert (
        'GRANT SELECT ON TABLE\n'
        '    "public"."customers",\n'
        '    "public"."departments",\n'
        '    "public"."employees",\n'
        '    "public"."products",\n'
        '    "public"."projects",\n'
        '    "public"."sales"'
    ) in sql
    assert "GRANT SELECT ON ALL TABLES" not in sql
    assert "NOINHERIT" in sql
    assert "NOBYPASSRLS" in sql
    assert "REVOKE %I FROM %I" not in sql
    assert "CASCADE" not in sql
    assert "DO $check_role_memberships$" in sql
    assert "DO $check_public_privileges$" in sql
    assert "aclexplode(" in sql
    assert "privilege.grantee = 0" in sql
    assert "privilege.privilege_type IN ('CREATE', 'TEMPORARY')" in sql
    assert "privilege.privilege_type = 'CREATE'" in sql
    assert "PUBLIC has database CREATE or TEMPORARY privileges" in sql
    assert "PUBLIC has CREATE privileges on an application schema" in sql
    assert "DO $check_public_function_execution$" in sql
    assert "namespace.nspname = 'public'" in sql
    assert "privilege.grantee = 0" in sql
    assert "privilege.privilege_type = 'EXECUTE'" in sql
    assert (
        "PUBLIC has EXECUTE privileges on public functions"
        in sql
    )
    assert "has_function_privilege(" in sql
    assert "'sql_agent_test_role', routine.oid, 'EXECUTE'" in sql
    assert (
        "SQL Agent role has EXECUTE privileges on public functions"
        in sql
    )
    assert (
        "has_schema_privilege('sql_agent_test_role', namespace.oid, 'USAGE')"
        in sql
    )
    assert (
        "has_schema_privilege('sql_agent_test_role', namespace.oid, 'CREATE')"
        in sql
    )
    assert "granted_role.rolname = " in sql
    assert "member_role.rolname = " in sql
    assert "manual review is required" in sql
    assert "REVOKE CREATE, TEMPORARY ON DATABASE" not in sql
    assert "REVOKE CREATE ON SCHEMA public FROM PUBLIC" not in sql
    assert "FROM PUBLIC" not in sql
