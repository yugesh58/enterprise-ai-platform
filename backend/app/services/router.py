from app.services.llm import llm
from app.prompts.router_prompt import ROUTER_PROMPT


def route_question(question: str):

    prompt = f"""
    {ROUTER_PROMPT}

    User Question:
    {question}
    """

    response = llm.invoke(prompt)

    return response.content.strip()