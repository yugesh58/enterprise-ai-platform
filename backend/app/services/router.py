from app.ai.llm import provider
from app.prompts.router_prompt import ROUTER_PROMPT


def route_question(question: str) -> str:
    prompt = f"""
    {ROUTER_PROMPT}

    User Question:
    {question}
    """

    response = provider.invoke(prompt)

    return response.content.strip().lower()
