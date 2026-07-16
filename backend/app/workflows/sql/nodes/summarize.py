from app.workflows.sql.summarizer import summarize_result


def summarize_node(state):
    """
    Generate a natural language summary of the SQL result.
    """

    summary = summarize_result(
        state["question"],
        state["result"],
    )

    return {
        "summary": summary
    }