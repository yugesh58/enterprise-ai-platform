from app.services.llm import llm
from app.prompts.sql_prompt import SQL_SYSTEM_PROMPT



def generate_sql(
    user_question: str,
    schema: str,
    memory: list
):

    recent_memory = memory[-3:]

    memory_text = ""

    for item in recent_memory:

        memory_text += f"""
User:
{item.get('question', '')}

Assistant:
{item.get('summary', '')}

"""

    prompt = f"""
{SQL_SYSTEM_PROMPT}

Database Schema:
{schema}

Conversation History:
{memory_text}

Current User Question:
{user_question}

Instructions:

1. Use conversation history to resolve references such as:
   - he
   - she
   - they
   - him
   - her
   - them
   - that employee
   - that department
   - previous result

2. If the question depends on previous context,
   combine the previous context with the current question.

3. Never treat pronouns as literal database values.

4. Generate ONLY valid SQLite SELECT statements.

5. Return ONLY SQL.
"""

    response = llm.invoke(prompt)

    sql_query = response.content.strip()

    sql_query = sql_query.replace(
        "```sql",
        ""
    )

    sql_query = sql_query.replace(
        "```",
        ""
    )

    return sql_query.strip()