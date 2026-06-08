def execute_pandas_query(
    pandas_code,
    df
):
    try:

        result = eval(
            pandas_code,
            {"df": df}
        )

        return result

    except Exception as e:

        return f"Error: {str(e)}"