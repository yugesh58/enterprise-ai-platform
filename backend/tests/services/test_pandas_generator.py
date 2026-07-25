from app.agents.analyst import analyst_query
from backend.app.services.pandas_generator import generate_panda_query

result = analyst_query()
columns = result["columns"]

panda_query = generate_panda_query("Which region has highest profit", columns)

print(panda_query)
