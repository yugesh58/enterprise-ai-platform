import re
from collections import deque

from app.storage.database.factory import DatabaseFactory


STOP_WORDS = {
    "what",
    "which",
    "who",
    "where",
    "when",
    "how",
    "many",
    "much",
    "show",
    "give",
    "tell",
    "me",
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "of",
    "for",
    "in",
    "on",
    "to",
    "from",
    "with",
    "and",
    "or",
    "by",
    "all",
    "get",
    "find",
    "list",
}


def _normalize_tokens(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())

    normalized = set()

    for token in tokens:
        parts = token.split("_")

        for part in parts:
            if len(part) <= 1:
                continue

            if part.endswith("ies") and len(part) > 4:
                part = part[:-3] + "y"
            elif part.endswith("s") and not part.endswith("ss"):
                part = part[:-1]

            if part not in STOP_WORDS:
                normalized.add(part)

    return normalized


def _schema_tokens(name: str) -> set[str]:
    return _normalize_tokens(name)


def _score_table(
    table_name: str,
    columns: list[dict],
    question_tokens: set[str],
) -> int:

    score = 0

    # Table-name matches are strong signals.
    table_tokens = _schema_tokens(table_name)
    score += len(table_tokens & question_tokens) * 3

    # Column-name matches are useful, but foreign-key IDs
    # should NOT determine semantic table relevance.
    for column in columns:
        column_name = column["name"].lower()

        if column_name.endswith("_id"):
            continue

        column_tokens = _schema_tokens(column_name)

        score += len(column_tokens & question_tokens) * 2

    return score

def _build_relationship_graph(schema: dict) -> dict[str, set[str]]:
    """
    Build an undirected FK graph.

    Example:

        sales -> employees
        employees -> departments

    becomes:

        sales <-> employees <-> departments
    """

    graph = {
        table: set()
        for table in schema
    }

    for table, details in schema.items():

        for foreign_key in details.get("foreign_keys", []):

            referenced_table = foreign_key["referred_table"]

            if referenced_table not in schema:
                continue

            graph[table].add(referenced_table)
            graph[referenced_table].add(table)

    return graph


def _shortest_path(
    graph: dict[str, set[str]],
    start: str,
    target: str,
) -> list[str] | None:
    """
    Find the shortest FK path between two tables.
    """

    if start == target:
        return [start]

    queue = deque([[start]])
    visited = {start}

    while queue:

        path = queue.popleft()
        current = path[-1]

        for neighbor in graph.get(current, set()):

            if neighbor in visited:
                continue

            new_path = path + [neighbor]

            if neighbor == target:
                return new_path

            visited.add(neighbor)
            queue.append(new_path)

    return None


def _find_minimal_table_set(
    selected_tables: set[str],
    relationship_graph: dict[str, set[str]],
) -> set[str]:
    """
    Connect relevant tables using shortest FK paths.

    Example:

        departments
              |
          employees
              |
            sales

    If departments and sales are relevant, employees is
    automatically included because it is required to connect them.
    """

    if len(selected_tables) <= 1:
        return selected_tables

    relevant_tables = set()

    selected_list = list(selected_tables)

    # Always preserve directly relevant tables.
    relevant_tables.update(selected_tables)

    # Connect every relevant table to the others using
    # the shortest FK path.
    for i in range(len(selected_list)):

        for j in range(i + 1, len(selected_list)):

            start = selected_list[i]
            target = selected_list[j]

            path = _shortest_path(
                relationship_graph,
                start,
                target,
            )

            if path:
                relevant_tables.update(path)

    return relevant_tables


def get_schema() -> dict:
    """
    Return the complete PostgreSQL schema.
    """

    db = DatabaseFactory.create("postgres")

    return db.get_schema()


def get_relevant_schema(question: str) -> dict:
    """
    Retrieve the minimal PostgreSQL schema required for the question.
    """

    schema = get_schema()

    question_tokens = _normalize_tokens(question)

    table_scores = {}

    for table_name, details in schema.items():

        score = _score_table(
            table_name,
            details.get("columns", []),
            question_tokens,
        )

        table_scores[table_name] = score

    selected_tables = {
    table
    for table, score in table_scores.items()
    if score >= 2
    }

    # Safety fallback.
    if not selected_tables:
        return schema

    relationship_graph = _build_relationship_graph(schema)

    minimal_tables = _find_minimal_table_set(
        selected_tables,
        relationship_graph,
    )

    return {
        table: schema[table]
        for table in schema
        if table in minimal_tables
    }