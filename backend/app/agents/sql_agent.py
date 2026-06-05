from app.graphs.sql_graph import sql_graph

def sql_agent_query(question):

    response=sql_graph.invoke(
    {
        "question": question,
        "retry_count":0
    }
    )
    return response