
import time

from app.ai.llm import provider
from app.prompts.router_prompt import ROUTER_PROMPT
from app.core.enums import AgentType
from app.core.logging import get_logger

logger = get_logger(__name__)


def route_question(question: str) -> str:
    """
    Route a user question to the appropriate agent.

    Supported agents:
    - RAG: document knowledge questions
    - SQL: structured database questions
    """

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    start_time = time.perf_counter()

    prompt = f"""
{ROUTER_PROMPT}

IMPORTANT:
Return ONLY one of these exact values:

rag
sql

Do not return explanations.
Do not return JSON.
Do not return agent names such as "RAG Agent" or "SQL Agent".

User Question:
{question}
"""

    try:
        response = provider.invoke(prompt)
        selected_agent = response.content.strip().lower()

        if selected_agent not in {
            AgentType.RAG,
            AgentType.SQL,
        }:
            raise ValueError(
                f"Invalid router response: {selected_agent}"
            )

        logger.info(
            "Agent routing completed",
            extra={
                "selected_agent": selected_agent,
                "duration_ms": round(
                    (time.perf_counter() - start_time) * 1000,
                    2,
                ),
            },
        )

        return selected_agent

    except Exception:
        logger.exception(
            "Agent routing failed",
            extra={
                "duration_ms": round(
                    (time.perf_counter() - start_time) * 1000,
                    2,
                ),
            },
        )
        raise
