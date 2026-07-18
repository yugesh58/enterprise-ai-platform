from app.services.pandas_generator import generate_pandas_query


def generate_pandas_node(state):
    pandas_code = generate_pandas_query(
        question=state["question"],
        columns=list(state["dataframe"].columns),
    )

    return {
        "pandas_code": pandas_code,
    }
