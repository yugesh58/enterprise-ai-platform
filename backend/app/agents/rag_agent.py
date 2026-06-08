from app.vectorstore.faiss_manager import load_vectorstore,retrieve_chunk
from app.services.rag_service import generate_rag_answer


def rag_agent_query(question):
    vectorstore=load_vectorstore()
    docs=retrieve_chunk(vectorstore,question)
    result=generate_rag_answer(docs,question)

    return result
