from langchain_core.documents import Document

from app.ai.embeddings import get_embeddings
from app.core.config import settings
from app.storage.vectorstore.factory import VectorStoreFactory


def retrieve_documents_node(state):
    question = state["question"]

    embeddings = get_embeddings()

    query_vector = embeddings.embed_query(question)

    vector_provider = VectorStoreFactory.get_provider()

    results = vector_provider.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=5,
    )

    documents = [
        Document(
            page_content=result["payload"]["text"],
            metadata={
                "document_id": result["payload"].get("document_id"),
                "source": result["payload"].get("source"),
                "page_number": result["payload"].get("page_number"),
                "chunk_index": result["payload"].get("chunk_index"),
                "score": result["score"],
            },
        )
        for result in results
    ]

    return {
        "documents": documents,
    }