from app.core.config import settings
from app.storage.vectorstore.providers.qdrant_provider import QdrantProvider

provider = QdrantProvider()

provider.connect()

provider.create_collection(
    collection_name=settings.QDRANT_COLLECTION,
    vector_size=1536,
)

print("✅ Collection created successfully!")

provider.close()