from uuid import UUID

from app.ai.embeddings import get_embeddings
from app.core.config import settings
from app.enums.document_status import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.schemas.embedding import EmbeddedChunk
from app.services.document.chunking_service import ChunkingService
from app.services.document.pdf_processing_service import PDFProcessingService
from app.services.document.vector_mapper import VectorMapper
from app.storage.file_storage.base import FileStorageProvider
from app.storage.vectorstore.base import VectorProvider


class DocumentIndexingService:
    """
    Handles document indexing into the vector database.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        storage: FileStorageProvider,
        pdf_processing_service: PDFProcessingService,
        chunking_service: ChunkingService,
        vector_provider: VectorProvider,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._pdf_processing_service = pdf_processing_service
        self._chunking_service = chunking_service
        self._vector_provider = vector_provider

        self._embeddings = get_embeddings()

    def index_document(
        self,
        document_id: UUID,
    ) -> None:
        """
        Process a document and index it into Qdrant.
        """

        document = self._repository.get_by_id(document_id)

        if document is None:
            raise ValueError(f"Document {document_id} not found.")

        self._repository.update_status(
            document_id,
            DocumentStatus.PROCESSING,
        )

        try:
            pdf_bytes = self._storage.read(document["storage_path"])

            pdf = self._pdf_processing_service.extract_document(
                pdf_bytes
            )

            chunks = self._chunking_service.chunk_document(
                document_id=document_id,
                source=document["filename"],
                pdf=pdf,
            )

            if not chunks:
                self._repository.update_status(
                    document_id,
                    DocumentStatus.INDEXED,
                )
                return

            texts = [chunk.text for chunk in chunks]

            embeddings = self._embeddings.embed_documents(
                texts
            )

            embedded_chunks = [
                EmbeddedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    embedding=embedding,
                    metadata=chunk.metadata,
                )
                for chunk, embedding in zip(
                    chunks,
                    embeddings,
                    strict=True,
                )
            ]

            vector_points = VectorMapper.to_vector_points(
                embedded_chunks
            )

            self._vector_provider.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=vector_points,
            )

            self._repository.update_status(
                document_id,
                DocumentStatus.INDEXED,
            )

        except Exception:

            self._repository.update_status(
                document_id,
                DocumentStatus.FAILED,
            )

            raise