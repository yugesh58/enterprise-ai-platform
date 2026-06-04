from typing_extensions import TypedDict
from app.memory.conversation_memory import(get_memory, add_to_memory)
from app.services.result_summarizer import summarize_result
from app.services.sql_generator import generate_sql
from app.database.query_executor import run_query
from app.database.schema_retriever import get_schema
from langgraph.graph import StateGraph, START, END

class SQLState(TypedDict):
    question: str
    memory:list
    summary:str
    schema: str
    sql_query: str
    validation_status: str
    validation_reason: str
    retry_count: int
    result: list

def retrieve_schema_node(state: SQLState):
    schema=get_schema()

    return {"schema":schema}

def memory_retriever_node(state:SQLState):
    memory=get_memory()
    return{"memory":memory}

def summarize_result_node(state:SQLState):
    summary=summarize_result(state["question"],state["result"])
    return{"summary":summary}

def memory_update_node(state:SQLState):
    add_to_memory(state["question"],state["sql_query"],state["summary"])
    return{}

def sql_generation_node(state:SQLState):
    question=state['question']
    schema=state["schema"]
    memory=state["memory"]
    sql_query=generate_sql(question, schema, memory)

    return {"sql_query": sql_query }

def validate_sql_node(state: SQLState):

    sql_query = state["sql_query"].strip()

    # Multiple SQL statements
    if ";" in sql_query[:-1]:

        return {
            "validation_status": "invalid",
            "validation_reason": "Multiple SQL statements detected."
        }

    dangerous_keywords = [
        "DROP",
        "DELETE",
        "TRUNCATE",
        "UPDATE",
        "ALTER",
        "INSERT"
    ]

    sql_upper = sql_query.upper()

    for keyword in dangerous_keywords:

        if keyword in sql_upper:

            return {
                "validation_status": "invalid",
                "validation_reason": f"{keyword} statements are not allowed."
            }

    if not sql_upper.startswith("SELECT"):

        return {
            "validation_status": "invalid",
            "validation_reason": "Only SELECT statements are allowed."
        }

    return {
        "validation_status": "valid",
        "validation_reason": ""
    }


def regenrate_sql_node(state: SQLState):

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

    from app.services.llm import llm

    response = llm.invoke(retry_prompt)

    sql_query = response.content.strip()

    sql_query = sql_query.replace("```sql", "")
    sql_query = sql_query.replace("```", "")

    retry_count = state.get("retry_count", 0) + 1

    return {
        "sql_query": sql_query.strip(),
        "retry_count": retry_count
    }

def validation_router(state: SQLState):

    if state["validation_status"] == "valid":
        return "execute_sql"

    if state.get("retry_count", 0) < 2:
        return "retry_sql"

    return "end"

def query_executor_node(state:SQLState):
    sql_query=state['sql_query']
    result=run_query(sql_query)

    return{"result":result}


graph_builder=StateGraph(SQLState)


#nodes
graph_builder.add_node("generate_sql",sql_generation_node)
graph_builder.add_node("memory_retriever_node",memory_retriever_node)
graph_builder.add_node("summarize_result_node",summarize_result_node)
graph_builder.add_node("memory_update_node",memory_update_node)
graph_builder.add_node("validate_sql",validate_sql_node)
graph_builder.add_node("execute_sql",query_executor_node)
graph_builder.add_node("retry_sql",regenrate_sql_node)
graph_builder.add_node("schema_node",retrieve_schema_node)


#edges
graph_builder.add_conditional_edges(
    "validate_sql",
    validation_router,
    {
        "execute_sql": "execute_sql",
        "retry_sql":"retry_sql",
        "end": END
    }
)


graph_builder.add_edge(START,"memory_retriever_node")
graph_builder.add_edge("memory_retriever_node","schema_node")
graph_builder.add_edge("schema_node","generate_sql")
graph_builder.add_edge("generate_sql","validate_sql")
graph_builder.add_edge("retry_sql","validate_sql")
graph_builder.add_edge("execute_sql","summarize_result_node")
graph_builder.add_edge("summarize_result_node","memory_update_node")
graph_builder.add_edge("memory_update_node",END)

sql_graph=graph_builder.compile()