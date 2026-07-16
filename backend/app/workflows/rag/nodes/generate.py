from app.services.rag_service import generate_rag_answer


def generate_answer_node(state):
    """
    Generate the final answer using the retrieved documents.
    """

    response = generate_rag_answer(
        state["documents"],
        state["question"],
    )

    return {
        "answer": response["answer"],
        "sources": response["sources"],
        "documents": state["documents"],
    }