from app.ai.llm import provider


def regenerate_sql_node(state):
    """
    Regenerate SQL when validation fails.
    """

    question = state["question"]
    schema = state["schema"]
    memory = state["memory"]
    validation_reason = state["validation_reason"]

    retry_prompt = f"""
The previous SQL query was rejected.

Reason:
{validation_reason}

Database Schema:
{schema}

Conversation History:
{memory}

User Question:
{question}

Rules:
1. Generate ONLY SQLite SELECT statements.
2. Do NOT use DELETE.
3. Do NOT use DROP.
4. Do NOT use UPDATE.
5. Do NOT use INSERT.
6. Do NOT use ALTER.
7. Return ONLY SQL.

Corrected SQL:
"""

    response = provider.invoke(retry_prompt)

    sql_query = response.content.replace("```sql", "").replace("```", "").strip()

    return {
        "sql_query": sql_query,
        "retry_count": state.get("retry_count", 0) + 1,
    }
