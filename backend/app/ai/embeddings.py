from app.ai.embedding_factory import EmbeddingFactory


embeddings = (
    EmbeddingFactory
    .get_provider()
    .get_embeddings()
)