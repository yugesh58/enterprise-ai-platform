
from app.core.config import settings
from app.storage.vectorstore.providers.qdrant_provider import QdrantProvider


def main() -> None:
    provider = QdrantProvider()

    try:
        provider.connect()
        provider.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vector_size=settings.QDRANT_VECTOR_SIZE,
        )
        print("Qdrant connection and collection verification successful!")
    finally:
        provider.close()


if __name__ == "__main__":
    main()
