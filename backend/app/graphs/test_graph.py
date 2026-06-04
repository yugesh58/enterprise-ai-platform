from app.graphs.sql_graph import sql_graph


result = sql_graph.invoke(
    {
        "question": "Show all employees",
        "retry_count": 0
    }
)

sql_graph.invoke(
    {
        "question": "Only those earning above 100000",
        "retry_count": 0
    }
)

print(sql_graph)