from app.services.llm import llm

def summarize_result(question:str, result:list):
    prompt=f"""
    
    You are a data analyst.

    Use ONLY the information provided in the query result.

    DO NOT invent facts.
    DO NOT assume job roles.
    DO NOT assume skills.
    DO NOT assume experience.
    DO NOT add information not present in the data.

    User Question:
    {question}

    Query Result:
    {result}

    Provide a concise summary based strictly on the result.

    """
    response=llm.invoke(prompt)

    return response.content.strip()