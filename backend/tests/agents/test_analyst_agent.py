from app.agents.analyst import analyst_query

response = analyst_query(
    "Which region has highest profit?"
)

print(response)