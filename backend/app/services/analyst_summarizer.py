from app.services.llm import llm

def analyst_summarizer(question,result):
    ANALYST_SUMMARIZER_PROMPT=f"""
    You are a result summarizer and your main job is to summarize the result based on the question asked by the user.

    User questio:
    {question}

    Result:
    {result}

    summarize the result and do not add an other information
    """
    summary=llm.invoke(ANALYST_SUMMARIZER_PROMPT)

    return summary.content.strip()