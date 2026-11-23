import time

from sqlglot import exp, parse
from sqlglot.errors import ParseError
from sqlglot.optimizer.scope import Scope, traverse_scope

from app.core.enums import ValidationStatus
from app.storage.database.sql_agent_policy import (
    APPROVED_SQL_AGENT_FUNCTIONS,
    APPROVED_SQL_AGENT_TABLES,
)


def validate_sql_node(state):
    """
    Validate LLM-generated SQL using PostgreSQL AST parsing.

    Policy:
    - Exactly one SQL statement.
    - Only read-only query expressions are allowed.
    - No DML, DDL, or administrative operations.
    - SELECT INTO and locking clauses are prohibited.
    - SQL comments are not allowed.
    - Only approved sample-data tables and safe functions are allowed.
    """

    start_time = time.perf_counter()

    sql_query = state.get("sql_query", "")

    def result(status, reason):
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return {
            "validation_status": status,
            "validation_reason": reason,
            "sql_validation_ms": elapsed_ms,
        }

    if not isinstance(sql_query, str) or not sql_query.strip():
        return result(
            ValidationStatus.INVALID,
            "SQL query is empty or invalid.",
        )

    try:
        statements = parse(sql_query.strip(), read="postgres")
    except ParseError:
        return result(
            ValidationStatus.INVALID,
            "SQL query contains invalid PostgreSQL syntax.",
        )

    statements = [statement for statement in statements if statement is not None]

    if len(statements) != 1:
        return result(
            ValidationStatus.INVALID,
            "Multiple SQL statements are not allowed.",
        )

    statement = statements[0]

    # Only query expressions such as SELECT, UNION, INTERSECT and EXCEPT.
    if not isinstance(statement, exp.Query):
        return result(
            ValidationStatus.INVALID,
            "Only SELECT queries are allowed.",
        )

    nodes = list(statement.walk())

    # Reject DML and DDL anywhere in the AST, including inside CTEs.
    if any(isinstance(node, (exp.DML, exp.DDL)) for node in nodes):
        return result(
            ValidationStatus.INVALID,
            "Write and database administration operations are not allowed.",
        )

    # SELECT INTO creates a table despite having a SELECT root.
    if any(
        isinstance(node, exp.Select) and node.args.get("into") is not None
        for node in nodes
    ):
        return result(
            ValidationStatus.INVALID,
            "SELECT INTO statements are not allowed.",
        )

    # Locking clauses can acquire database locks and are prohibited.
    if any(
        isinstance(node, exp.Select) and node.args.get("locks")
        for node in nodes
    ):
        return result(
            ValidationStatus.INVALID,
            "SELECT locking clauses are not allowed.",
        )

    # Preserve the existing policy that rejects SQL comments.
    if any(node.comments for node in nodes):
        return result(
            ValidationStatus.INVALID,
            "SQL comments are not allowed.",
        )

    for node in nodes:
        if isinstance(node, exp.Func):
            if (
                isinstance(node, exp.Anonymous)
                or node.sql_name().upper()
                not in APPROVED_SQL_AGENT_FUNCTIONS
            ):
                return result(
                    ValidationStatus.INVALID,
                    "The SQL query contains a disallowed function.",
                )

    for scope in traverse_scope(statement):
        for table in scope.tables:
            source = scope.sources.get(table.alias_or_name)

            if not table.db and not table.catalog and isinstance(source, Scope):
                continue

            if (
                table.catalog
                or table.db.casefold() not in {"", "public"}
                or table.name.casefold() not in APPROVED_SQL_AGENT_TABLES
            ):
                return result(
                    ValidationStatus.INVALID,
                    "The SQL query references a non-approved table.",
                )

    return result(ValidationStatus.VALID, "")


def validation_router(state):
    """Route the workflow based on SQL validation."""

    if state["validation_status"] == ValidationStatus.VALID:
        return "execute_sql"

    if state.get("retry_count", 0) < 2:
        return "retry_sql"

    return "end"