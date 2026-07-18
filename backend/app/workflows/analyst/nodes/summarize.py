from app.services.analyst_summarizer import analyst_summarizer


def summarize_node(state):
    summary = analyst_summarizer(
        state["question"],
        state["result"],
    )

    return {
        "summary": summary,
    }