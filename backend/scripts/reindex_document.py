from uuid import UUID

from app.storage.database.connection import get_connection
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.document.document_indexing_service import DocumentIndexingService
from app.services.document.chunking_service import ChunkingService
from app.services.document.pdf_processing_service import PDFProcessingService
from app.api.dependencies.storage import get_storage_provider
from app.api.dependencies.vectorstore import get_vector_provider


DOCUMENT_ID = UUID(
    "fca77fcc-a0ce-46c9-bec5-414e23014ad5"
)


def main():
    connection = get_connection()

    try:
        repository = DocumentRepository(connection)

        chunk_repository = DocumentChunkRepository(connection)

        service = DocumentIndexingService(
            repository=repository,
            chunk_repository=chunk_repository,
            storage=get_storage_provider(),
            pdf_processing_service=PDFProcessingService(),
            chunking_service=ChunkingService(),
            vector_provider=get_vector_provider(),
        )

        service.index_document(DOCUMENT_ID)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
