from langchain_community.vectorstores import FAISS

from app.ai.embeddings import get_embeddings
from app.core.config import settings

FAISS_PATH = settings.VECTOR_DB_PATH


def create_vectorstore(documents):

    vector_store = FAISS.from_documents(
        documents,
        embedding=get_embeddings(),
    )

    return vector_store


def add_documents_to_vectorstore(
    vectorstore,
    documents,
):

    vectorstore.add_documents(documents)

    return vectorstore


def save_vectorstore(vectorstore):

    vectorstore.save_local(FAISS_PATH)


def load_vectorstore():

    return FAISS.load_local(
        FAISS_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )


def retrieve_chunk(
    vectorstore,
    question,
    k=3,
):

    return vectorstore.similarity_search(
        question,
        k=k,
    )
