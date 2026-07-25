from langgraph.graph import END, START, StateGraph

from app.workflows.sql.nodes.execute_sql import execute_sql_node
from app.workflows.sql.nodes.generate_sql import generate_sql_node
from app.workflows.sql.nodes.memory import retrieve_memory_node
from app.workflows.sql.nodes.retry import regenerate_sql_node
from app.workflows.sql.nodes.schema import retrieve_schema_node
from app.workflows.sql.nodes.summarize import summarize_node
from app.workflows.sql.nodes.update_memory import update_memory_node
from app.workflows.sql.nodes.validate_sql import (
    validate_sql_node,
    validation_router,
)
from app.workflows.sql.state import SQLState

graph_builder = StateGraph(SQLState)

# Nodes
graph_builder.add_node("memory", retrieve_memory_node)
graph_builder.add_node("schema", retrieve_schema_node)
graph_builder.add_node("generate_sql", generate_sql_node)
graph_builder.add_node("validate_sql", validate_sql_node)
graph_builder.add_node("retry_sql", regenerate_sql_node)
graph_builder.add_node("execute_sql", execute_sql_node)
graph_builder.add_node("summarize", summarize_node)
graph_builder.add_node("update_memory", update_memory_node)

# Edges
graph_builder.add_edge(START, "memory")
graph_builder.add_edge("memory", "schema")
graph_builder.add_edge("schema", "generate_sql")
graph_builder.add_edge("generate_sql", "validate_sql")
graph_builder.add_edge("retry_sql", "validate_sql")
graph_builder.add_edge("execute_sql", "summarize")
graph_builder.add_edge("summarize", "update_memory")
graph_builder.add_edge("update_memory", END)

# Conditional Routing
graph_builder.add_conditional_edges(
    "validate_sql",
    validation_router,
    {
        "execute_sql": "execute_sql",
        "retry_sql": "retry_sql",
        "end": END,
    },
)

sql_graph = graph_builder.compile()
