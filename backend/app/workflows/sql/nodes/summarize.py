from app.workflows.sql.summarizer import summarize_result


def summarize_node(state):
    """
    Generate a natural language answer from the SQL result.
    """

    answer = summarize_result(
        state["question"],
        state["result"],
    )

    return {
        "summary": answer,
        "answer": answer,
    }