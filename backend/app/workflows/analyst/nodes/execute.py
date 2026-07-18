from app.services.pandas_executor import execute_pandas_query


def execute_node(state):
    result = execute_pandas_query(
        pandas_code=state["pandas_code"],
        df=state["dataframe"],
    )

    return {
        "result": result,
    }