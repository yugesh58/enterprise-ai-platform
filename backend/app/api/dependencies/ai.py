from app.ai.embeddings import get_embeddings


def get_embedding_model():
    """
    Returns the configured embedding model.
    """

    return get_embeddings()