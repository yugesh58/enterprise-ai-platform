from app.storage.vectorstore.base import VectorProvider
from app.storage.vectorstore.factory import VectorStoreFactory


def get_vector_provider() -> VectorProvider:
    """
    Returns the configured vector provider.
    """

    return VectorStoreFactory.get_provider()