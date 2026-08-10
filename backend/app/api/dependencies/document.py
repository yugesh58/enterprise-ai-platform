from fastapi import Depends

from app.services.document.document_chat_service import (
    DocumentChatService,
)
from app.services.document.document_retriever_service import (
    DocumentRetriever,
)
from app.services.document.document_search_service import (
    DocumentSearchService,
)
from app.api.dependencies.repositories import get_document_repository
from app.api.dependencies.storage import get_storage_provider
from app.api.dependencies.vectorstore import get_vector_provider
from app.services.document.chunking_service import ChunkingService
from app.services.document.document_indexing_service import DocumentIndexingService
from app.services.document.document_service import DocumentService
from app.services.document.pdf_processing_service import PDFProcessingService


def get_document_search_service() -> DocumentSearchService:
    return DocumentSearchService(
        vector_provider=get_vector_provider(),
    )


def get_document_retriever() -> DocumentRetriever:
    return DocumentRetriever(
        search_service=get_document_search_service(),
    )


def get_document_chat_service() -> DocumentChatService:
    return DocumentChatService(
        retriever=get_document_retriever(),
    )


def get_document_service(
    repository=Depends(get_document_repository),
    storage=Depends(get_storage_provider),
) -> DocumentService:
    return DocumentService(
        repository=repository,
        storage=storage,
    )


def get_document_indexing_service(
    repository=Depends(get_document_repository),
    storage=Depends(get_storage_provider),
) -> DocumentIndexingService:
    return DocumentIndexingService(
        repository=repository,
        storage=storage,
        pdf_processing_service=PDFProcessingService(),
        chunking_service=ChunkingService(),
        vector_provider=get_vector_provider(),
    )
