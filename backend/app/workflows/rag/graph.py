from langgraph.graph import START, END, StateGraph

from app.workflows.rag.state import RAGState

from app.workflows.rag.nodes.retrieve import retrieve_documents_node
from app.workflows.rag.nodes.generate import generate_answer_node


graph_builder = StateGraph(RAGState)

graph_builder.add_node(
    "retrieve",
    retrieve_documents_node,
)

graph_builder.add_node(
    "generate",
    generate_answer_node,
)

graph_builder.add_edge(
    START,
    "retrieve",
)

graph_builder.add_edge(
    "retrieve",
    "generate",
)

graph_builder.add_edge(
    "generate",
    END,
)

rag_graph = graph_builder.compile()