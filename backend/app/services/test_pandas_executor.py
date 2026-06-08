import pandas as pd

from app.agents.analyst_agent import analyst_agent_query
from app.services.panda_generator import generate_pandas_query
from app.services.pandas_executor import execute_pandas_query
from app.services.analyst_summarizer import analyst_summarizer

df = pd.read_csv(
    "app/uploads/sales.csv"
)

columns = list(df.columns)

pandas_code = generate_pandas_query(
    "Which region has highest profit?",
    columns
)

print("\nGenerated Code:\n")
print(pandas_code)

result = execute_pandas_query(
    pandas_code,
    df
)

summary=analyst_summarizer("Which region has highest profit?",result)
print(summary)
