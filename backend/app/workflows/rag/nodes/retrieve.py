from app.storage.vectorstore.faiss_manager import (
    load_vectorstore,
    retrieve_chunk,
)


def retrieve_documents_node(state):

    vectorstore = load_vectorstore()

    documents = retrieve_chunk(
        vectorstore,
        state["question"],
    )

    return {"documents": documents}
