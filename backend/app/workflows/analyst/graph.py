from app.workflows.analyst.nodes.load_dataset import load_data_node
from langgraph.graph import END, START, StateGraph

from app.workflows.analyst.nodes.chart import chart_node
from app.workflows.analyst.nodes.execute import execute_node
from app.workflows.analyst.nodes.generate_pandas import generate_pandas_node
from app.workflows.analyst.nodes.summarize import summarize_node
from app.workflows.analyst.state import AnalystState

graph_builder = StateGraph(AnalystState)

graph_builder.add_node("load_data", load_data_node)
graph_builder.add_node("generate_pandas", generate_pandas_node)
graph_builder.add_node("execute", execute_node)
graph_builder.add_node("chart", chart_node)
graph_builder.add_node("summarize", summarize_node)

graph_builder.add_edge(START, "load_data")
graph_builder.add_edge("load_data", "generate_pandas")
graph_builder.add_edge("generate_pandas", "execute")
graph_builder.add_edge("execute", "chart")
graph_builder.add_edge("chart", "summarize")
graph_builder.add_edge("summarize", END)

analyst_graph = graph_builder.compile()
