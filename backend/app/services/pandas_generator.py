from app.ai.llm import provider
from app.prompts.analyst_prompt import ANALYST_SYSTEM_PROMPT


def generate_pandas_query(question: str, columns: list):
    SYSTEM_PROMPT = f"""
    
    Instructions:
    {ANALYST_SYSTEM_PROMPT}

    User question:
    {question}

    Available dataframe columns:
    {columns}

    """

    result = provider.invoke(SYSTEM_PROMPT)

    return result.content.strip()
