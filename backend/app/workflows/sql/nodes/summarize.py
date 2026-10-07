import time

from app.workflows.sql.summarizer import summarize_result


LIST_KEYWORDS = {
    "list",
    "show",
    "top",
    "bottom",
    "highest",
    "lowest",
    "all",
    "which",
    "what are",
    "give me",
    "find",
    "employees",
    "departments",
    "products",
    "customers",
    "projects",
}


def expects_multiple_results(question: str) -> bool:
    """
    Determine whether the user's question naturally expects
    multiple records.
    """

    normalized = question.lower().strip()

    return any(
        keyword in normalized
        for keyword in LIST_KEYWORDS
    )


def summarize_node(state):
    start_time = time.perf_counter()

    result = state.get("result", [])
    question = state.get("question", "")

    if not result:
        answer = "No matching records were found."

    elif len(result) > 1 and not expects_multiple_results(question):
        answer = (
            f"Multiple matching records were found ({len(result)}). "
            "The result is ambiguous, so a single answer cannot be determined."
        )

    else:
        answer = summarize_result(
            question,
            result,
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "summary": answer,
        "answer": answer,
        "summarization_ms": elapsed_ms,
    }