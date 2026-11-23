import pytest

from app.core.enums import ValidationStatus
from app.workflows.sql.nodes.validate_sql import (
    validate_sql_node,
    validation_router,
)


def test_valid_select():
    result = validate_sql_node({
        "sql_query": "SELECT * FROM employees",
        "retry_count": 0,
    })

    assert result["validation_status"] == ValidationStatus.VALID
    assert result["validation_reason"] == ""
    assert result["sql_validation_ms"] >= 0


def test_valid_select_with_trailing_semicolon():
    result = validate_sql_node({
        "sql_query": "SELECT * FROM employees;",
        "retry_count": 0,
    })

    assert result["validation_status"] == ValidationStatus.VALID


def test_valid_with_query():
    result = validate_sql_node({
        "sql_query": """
        WITH top_employees AS (
            SELECT employee_id, salary
            FROM employees
        )
        SELECT *
        FROM top_employees
        """,
        "retry_count": 0,
    })

    assert result["validation_status"] == ValidationStatus.VALID


def test_valid_select_from_approved_sample_tables_and_safe_functions():
    result = validate(
        """
        SELECT d.department_name, COUNT(*) AS employee_count,
               ROUND(AVG(e.salary)) AS average_salary
        FROM public.departments AS d
        JOIN public.employees AS e
          ON e.department_id = d.department_id
        GROUP BY d.department_name
        """
    )

    assert result["validation_status"] == ValidationStatus.VALID


def test_valid_cte_can_reference_approved_tables():
    result = validate(
        """
        WITH active_sales AS (
            SELECT amount FROM sales WHERE sale_date >= CURRENT_DATE
        )
        SELECT SUM(amount) FROM active_sales
        """
    )

    assert result["validation_status"] == ValidationStatus.VALID


def test_delete_is_rejected():
    result = validate_sql_node({
        "sql_query": "DELETE FROM employees",
        "retry_count": 0,
    })

    assert result["validation_status"] == ValidationStatus.INVALID


def test_insert_is_rejected():
    result = validate(
        "INSERT INTO employees (employee_id) VALUES (1)"
    )

    assert result["validation_status"] == ValidationStatus.INVALID


def test_update_is_rejected():
    result = validate_sql_node({
        "sql_query": "UPDATE employees SET salary = 0",
        "retry_count": 0,
    })

    assert result["validation_status"] == ValidationStatus.INVALID


def test_alter_is_rejected():
    result = validate("ALTER TABLE employees ADD COLUMN unsafe TEXT")

    assert result["validation_status"] == ValidationStatus.INVALID


def test_drop_is_rejected():
    result = validate_sql_node({
        "sql_query": "DROP TABLE employees",
        "retry_count": 0,
    })

    assert result["validation_status"] == ValidationStatus.INVALID


def test_multiple_statements_are_rejected():
    result = validate_sql_node({
        "sql_query": "SELECT * FROM employees; SELECT * FROM departments",
        "retry_count": 0,
    })

    assert result["validation_status"] == ValidationStatus.INVALID
    assert "Multiple SQL statements" in result["validation_reason"]


def test_comments_are_rejected():
    result = validate_sql_node({
        "sql_query": "SELECT * FROM employees -- dangerous comment",
        "retry_count": 0,
    })

    assert result["validation_status"] == ValidationStatus.INVALID


def test_empty_sql_is_rejected():
    result = validate_sql_node({
        "sql_query": "",
        "retry_count": 0,
    })

    assert result["validation_status"] == ValidationStatus.INVALID


def test_invalid_sql_retries():
    state = {
        "validation_status": ValidationStatus.INVALID,
        "retry_count": 0,
    }

    assert validation_router(state) == "retry_sql"


def test_invalid_sql_stops_after_two_retries():
    state = {
        "validation_status": ValidationStatus.INVALID,
        "retry_count": 2,
    }

    assert validation_router(state) == "end"
def validate(query):
    return validate_sql_node({
        "sql_query": query,
        "retry_count": 0,
    })


def test_delete_inside_cte_is_rejected():
    result = validate(
        "WITH x AS (DELETE FROM employees RETURNING *) "
        "SELECT * FROM x"
    )
    assert result["validation_status"] == ValidationStatus.INVALID


def test_insert_inside_cte_is_rejected():
    result = validate(
        "WITH x AS (INSERT INTO employees VALUES (1) RETURNING *) "
        "SELECT * FROM x"
    )
    assert result["validation_status"] == ValidationStatus.INVALID


def test_select_into_is_rejected():
    result = validate("SELECT * INTO new_table FROM employees")
    assert result["validation_status"] == ValidationStatus.INVALID


def test_for_update_is_rejected():
    result = validate("SELECT * FROM employees FOR UPDATE")
    assert result["validation_status"] == ValidationStatus.INVALID


def test_for_share_is_rejected():
    result = validate("SELECT * FROM employees FOR SHARE")
    assert result["validation_status"] == ValidationStatus.INVALID


def test_explain_is_rejected():
    result = validate("EXPLAIN SELECT * FROM employees")
    assert result["validation_status"] == ValidationStatus.INVALID


def test_copy_is_rejected():
    result = validate("COPY employees TO '/tmp/employees.csv'")
    assert result["validation_status"] == ValidationStatus.INVALID


def test_union_is_allowed():
    result = validate("SELECT 1 UNION SELECT 2")
    assert result["validation_status"] == ValidationStatus.VALID


def test_intersect_is_allowed():
    result = validate("SELECT 1 INTERSECT SELECT 2")
    assert result["validation_status"] == ValidationStatus.VALID


def test_except_is_allowed():
    result = validate("SELECT 1 EXCEPT SELECT 2")
    assert result["validation_status"] == ValidationStatus.VALID


def test_blocked_keyword_inside_string_is_allowed():
    result = validate("SELECT 'DROP TABLE' AS message")
    assert result["validation_status"] == ValidationStatus.VALID


def test_semicolon_inside_string_is_allowed():
    result = validate("SELECT 'hello; world' AS message")
    assert result["validation_status"] == ValidationStatus.VALID


def test_malformed_sql_is_rejected():
    result = validate("SELECT FROM WHERE")
    assert result["validation_status"] == ValidationStatus.INVALID


@pytest.mark.parametrize(
    "table_name",
    [
        "llm_usage_events",
        "application_alembic_version",
        "documents",
        "information_schema.tables",
        "pg_catalog.pg_roles",
    ],
)
def test_non_approved_tables_are_rejected(table_name):
    result = validate(f"SELECT * FROM {table_name}")

    assert result["validation_status"] == ValidationStatus.INVALID


@pytest.mark.parametrize(
    "function_call",
    [
        "pg_sleep(1)",
        "pg_read_file('/etc/passwd')",
        "set_config('statement_timeout', '0', false)",
        "current_setting('statement_timeout')",
        "nextval('employee_id_seq')",
        "setval('employee_id_seq', 1)",
        "generate_series(1, 1000000)",
        "CAST('1' AS integer)",
        "'1'::integer",
    ],
)
def test_dangerous_or_unapproved_functions_are_rejected(function_call):
    result = validate(f"SELECT {function_call}")

    assert result["validation_status"] == ValidationStatus.INVALID


def test_schema_qualified_functions_are_rejected():
    result = validate("SELECT public.lower(employee_name) FROM employees")

    assert result["validation_status"] == ValidationStatus.INVALID


def test_unapproved_table_inside_cte_is_rejected():
    result = validate(
        "WITH safe_name AS (SELECT * FROM llm_usage_events) "
        "SELECT * FROM safe_name"
    )

    assert result["validation_status"] == ValidationStatus.INVALID