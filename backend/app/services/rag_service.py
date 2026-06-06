from app.services.llm import llm


def generate_rag_answer(
    docs,
    question
):
    
    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    sources = list(
        set(
            [
                doc.metadata.get("source", "Unknown")
                for doc in docs
            ]
        )
    )

    prompt = f"""
    Answer the user's question using ONLY the provided context.

    Context:
    {context}

    Question:
    {question}

    If the answer is not present in the context,
    say exactly:

    "I could not find that information in the uploaded documents."
    """

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "sources": sources
    }