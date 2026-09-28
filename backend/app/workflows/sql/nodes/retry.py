from app.ai.llm import provider


def regenerate_sql_node(state):
    """
    Regenerate SQL when validation or database execution fails.
    """

    question = state["question"]
    schema = state["schema"]
    memory = state["memory"]

    validation_reason = state.get("validation_reason", "")
    execution_error = state.get("execution_error", "")

    retry_prompt = f"""
The previous SQL query could not be completed.

Validation Error:
{validation_reason}

Database Execution Error:
{execution_error}

Database Schema:
{schema}

Conversation History:
{memory}

User Question:
{question}

Your task is to generate a corrected SQL query that answers
the user's question.

Rules:
1. Generate exactly ONE SQLite SELECT statement.
2. Use ONLY tables and columns present in the database schema.
3. Do NOT use INSERT.
4. Do NOT use UPDATE.
5. Do NOT use DELETE.
6. Do NOT use DROP.
7. Do NOT use ALTER.
8. Do NOT use TRUNCATE.
9. Do NOT use CREATE.
10. Do NOT use REPLACE.
11. Do NOT use MERGE.
12. Do NOT use UPSERT.
13. Do NOT use GRANT.
14. Do NOT use REVOKE.
15. Do NOT use ATTACH.
16. Do NOT use DETACH.
17. Do NOT use VACUUM.
18. Do NOT use PRAGMA.
19. Do NOT generate multiple SQL statements.
20. Return ONLY SQL.
21. Do not include markdown fences.

Corrected SQL:
"""

    response = provider.invoke(retry_prompt)

    sql_query = (
        response.content
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )

    return {
        "sql_query": sql_query,
        "retry_count": state.get("retry_count", 0) + 1,
    }