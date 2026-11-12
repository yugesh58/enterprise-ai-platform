
import time
from collections.abc import Mapping
from typing import Any
from datetime import date, datetime
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

COMPLEX_KEYWORDS = {
    "compare",
    "comparison",
    "why",
    "explain",
    "analyze",
    "analysis",
    "trend",
    "increase",
    "decrease",
    "difference",
    "impact",
    "correlation",
    "relationship",
    "performance",
}


def expects_multiple_results(question: str) -> bool:
    """Determine whether the question naturally expects multiple records."""

    normalized = question.lower().strip()

    return any(
        keyword in normalized
        for keyword in LIST_KEYWORDS
    )


def _is_simple_list_question(question: str) -> bool:
    """Identify straightforward list and ranking questions."""

    normalized = question.lower().strip()

    if any(keyword in normalized for keyword in COMPLEX_KEYWORDS):
        return False

    return expects_multiple_results(normalized)


def _has_prior_conversation(
    memory: list,
    question: str,
) -> bool:
    """Check whether memory contains messages preceding the current question."""

    normalized_question = question.strip()

    for message in memory:
        if (
            message.get("role") == "user"
            and message.get("content", "").strip() == normalized_question
        ):
            continue

        return True

    return False


def _has_scalar_values(result: list) -> bool:
    """Check whether all result values can be safely formatted as text."""

    if not isinstance(result, list) or not result:
        return False

    if len(result) > 10:
        return False

    supported_types = (
        str,
        int,
        float,
        bool,
        date,
        datetime,
    )

    for row in result:
        if not isinstance(row, Mapping) or not row or len(row) > 8:
            return False

        for value in row.values():
            if value is not None and not isinstance(
                value,
                supported_types,
            ):
                return False

    return True

def _format_deterministic_result(result: list[dict[str, Any]]) -> str:
    """Format simple tabular results without an LLM call."""

    lines = []

    for index, row in enumerate(result, start=1):
        fields = [
            f"{column}: {value if value is not None else 'N/A'}"
            for column, value in row.items()
        ]

        lines.append(f"{index}. " + "; ".join(fields))

    return "Here are the results:\n\n" + "\n".join(lines)


def summarize_node(state):
    start_time = time.perf_counter()

    result = state.get("result", [])
    question = state.get("question", "")
    memory = state.get("memory", [])

    has_prior_context = _has_prior_conversation(
        memory,
        question,
    )
    if not result:
        answer = "No matching records were found."

    elif len(result) > 1 and not expects_multiple_results(question):
        answer = (
            f"Multiple matching records were found ({len(result)}). "
            "The result is ambiguous, so a single answer cannot be determined."
        )

    elif (
        not has_prior_context
        and _is_simple_list_question(question)
        and _has_scalar_values(result)
    ):
        answer = _format_deterministic_result(result)

    else:
        answer = summarize_result(question, result)

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "summary": answer,
        "answer": answer,
        "summarization_ms": elapsed_ms,
    }
