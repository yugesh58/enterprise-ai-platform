from app.agents.analyst_agent import analyst_agent_query

response = analyst_agent_query(
    "Which region has highest profit?"
)

print(response)