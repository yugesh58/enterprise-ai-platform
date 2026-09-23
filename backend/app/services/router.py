from app.ai.llm import provider
from app.prompts.router_prompt import ROUTER_PROMPT
from app.core.enums import AgentType


def route_question(question: str) -> str:
    """
    Route a user question to the appropriate agent.

    Supported agents:
    - RAG: document knowledge questions
    - SQL: structured database questions

    The router uses the LLM for classification but strictly
    validates the returned agent type.
    """

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

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

    response = provider.invoke(prompt)

    selected_agent = response.content.strip().lower()

    if selected_agent not in {
        AgentType.RAG,
        AgentType.SQL,
    }:
        raise ValueError(
            f"Invalid router response: {selected_agent}"
        )

    return selected_agent