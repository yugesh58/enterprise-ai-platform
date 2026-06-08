import pandas as pd

def analyst_agent_query():

    df = pd.read_csv(
        "app/uploads/sales.csv"
    )

    return {
        "rows": len(df),
        "columns": list(df.columns),
        "sample": df.head().to_dict(
            orient="records"
        )
    }