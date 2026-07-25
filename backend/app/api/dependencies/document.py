from fastapi import Depends

from app.api.dependencies.repositories import (
    get_document_repository,
)
from app.api.dependencies.storage import (
    get_storage_provider,
)
from app.api.dependencies.vectorstore import (
    get_vector_provider,
)
from app.repositories.document_repository import (
    DocumentRepository,
)
from app.services.document.chunking_service import (
    ChunkingService,
)
from app.services.document.document_indexing_service import (
    DocumentIndexingService,
)
from app.services.document.document_service import (
    DocumentService,
)
from app.services.document.pdf_processing_service import (
    PDFProcessingService,
)
from app.storage.file_storage.base import (
    FileStorageProvider,
)
from app.storage.vectorstore.base import (
    VectorProvider,
)


def get_pdf_processing_service() -> PDFProcessingService:
    return PDFProcessingService()


def get_chunking_service() -> ChunkingService:
    return ChunkingService()


def get_document_service(
    repository: DocumentRepository = Depends(
        get_document_repository
    ),
    storage: FileStorageProvider = Depends(
        get_storage_provider
    ),
) -> DocumentService:

    return DocumentService(
        repository=repository,
        storage=storage,
    )


def get_document_indexing_service(
    repository: DocumentRepository = Depends(
        get_document_repository
    ),
    storage: FileStorageProvider = Depends(
        get_storage_provider
    ),
    pdf_processing_service: PDFProcessingService = Depends(
        get_pdf_processing_service
    ),
    chunking_service: ChunkingService = Depends(
        get_chunking_service
    ),
    vector_provider: VectorProvider = Depends(
        get_vector_provider
    ),
) -> DocumentIndexingService:

    return DocumentIndexingService(
        repository=repository,
        storage=storage,
        pdf_processing_service=pdf_processing_service,
        chunking_service=chunking_service,
        vector_provider=vector_provider,
    )

    return DocumentIndexingService(
        repository=repository,
        storage=storage,
        pdf_processing_service=PDFProcessingService(),
        chunking_service=ChunkingService(),
        vector_provider=vector_provider,
    )