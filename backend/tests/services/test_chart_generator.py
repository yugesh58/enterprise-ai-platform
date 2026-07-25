# test_chart_generator.py

import pandas as pd

from app.services.chart_generator import generate_chart
from app.services.pandas_executor import execute_pandas_query
from app.services.pandas_generator import generate_pandas_query

df = pd.read_csv("app/uploads/sales.csv")

columns = list(df.columns)

query = generate_pandas_query("Show total profit by region", columns)

print(query)

result = execute_pandas_query(query, df)

chart_path = generate_chart(result)

print(chart_path)
