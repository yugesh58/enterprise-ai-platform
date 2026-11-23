"""Database objects the SQL Agent is permitted to query."""

APPROVED_SQL_AGENT_TABLES = frozenset(
    {
        "customers",
        "departments",
        "employees",
        "products",
        "projects",
        "sales",
    }
)

APPROVED_SQL_AGENT_FUNCTIONS = frozenset(
    {
        "ABS",
        "AVG",
        "BTRIM",
        "CEIL",
        "COALESCE",
        "CONCAT",
        "COUNT",
        "CURRENT_DATE",
        "CURRENT_TIMESTAMP",
        "EXTRACT",
        "FLOOR",
        "GREATEST",
        "LEAST",
        "LENGTH",
        "LOWER",
        "MAX",
        "MIN",
        "NULLIF",
        "POSITION",
        "ROUND",
        "SUBSTRING",
        "SUM",
        "TIMESTAMP_TRUNC",
        "TRIM",
        "UPPER",
    }
)
