import pandas as pd
from app.services.pandas_generator import generate_pandas_query
from app.services.pandas_executor import execute_pandas_query
from app.services.chart_generator import generate_chart
from app.services.analyst_summarizer import analyst_summarizer

def analyst_agent_query(question):

    df = pd.read_csv(
        "app/uploads/sales.csv"
    )
    columns=list(df.columns)

    pandas_code=generate_pandas_query(question=question,columns=columns)

    result=execute_pandas_query(pandas_code=pandas_code,df=df)

    chart_path=generate_chart(result=result)

    summary=analyst_summarizer(question,result)

    return {
        "agent": "ANALYST_AGENT",
        "question": question,
        "generated_code": pandas_code,
        "summary": summary,
        "chart_path": chart_path,
        "result": result
    }
