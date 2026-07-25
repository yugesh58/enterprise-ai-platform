from app.ai.embedding_factory import EmbeddingFactory

def get_embeddings():
    return EmbeddingFactory.get_provider().get_embeddings()