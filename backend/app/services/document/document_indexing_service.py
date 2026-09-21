import time
import traceback
from uuid import UUID

from app.ai.embeddings import get_embeddings
from app.core.config import settings
from app.enums.document_status import DocumentStatus
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.embedding import EmbeddedChunk
from app.services.document.chunking_service import ChunkingService
from app.services.document.pdf_processing_service import PDFProcessingService
from app.services.document.vector_mapper import VectorMapper
from app.storage.file_storage.base import FileStorageProvider
from app.storage.vectorstore.base import VectorProvider


class DocumentIndexingService:
    """
    Handles document indexing into PostgreSQL and Qdrant.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        chunk_repository: DocumentChunkRepository,
        storage: FileStorageProvider,
        pdf_processing_service: PDFProcessingService,
        chunking_service: ChunkingService,
        vector_provider: VectorProvider,
    ) -> None:
        self._repository = repository
        self._chunk_repository = chunk_repository
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
        Process a document and index it into PostgreSQL and Qdrant.
        """

        print("\n" + "=" * 80)
        print(f"🚀 Starting indexing for document: {document_id}")
        print("=" * 80)

        start_time = time.time()

        document = self._repository.get_by_id(document_id)

        if document is None:
            raise ValueError(f"Document {document_id} not found.")

        print(f"📄 Filename: {document['filename']}")

        self._repository.update_status(
            document_id,
            DocumentStatus.PROCESSING,
        )

        try:
            # -----------------------------------------------------------------
            # 1. Read document
            # -----------------------------------------------------------------
            print("\n[1/7] Reading document from storage...")

            pdf_bytes = self._storage.read(
                document["storage_path"]
            )

            print(
                f"✅ Read {len(pdf_bytes):,} bytes"
            )

            # -----------------------------------------------------------------
            # 2. Extract PDF
            # -----------------------------------------------------------------
            print("\n[2/7] Extracting PDF...")

            pdf = self._pdf_processing_service.extract_document(
                pdf_bytes
            )

            print(
                f"✅ Pages extracted: {len(pdf.pages)}"
            )

            # -----------------------------------------------------------------
            # 3. Create chunks
            # -----------------------------------------------------------------
            print("\n[3/7] Creating chunks...")

            chunks = self._chunking_service.chunk_document(
                document_id=document_id,
                source=document["filename"],
                pdf=pdf,
            )

            print(
                f"✅ Generated {len(chunks)} chunks"
            )

            if not chunks:
                print("⚠️ No chunks generated.")

                self._repository.update_status(
                    document_id,
                    DocumentStatus.INDEXED,
                )

                return

            # -----------------------------------------------------------------
            # 4. Prepare embedding input
            # -----------------------------------------------------------------
            print(
                "\n[4/7] Preparing text for embeddings..."
            )

            texts = [
                chunk.text
                for chunk in chunks
            ]

            print(
                f"✅ Sending {len(texts)} chunks "
                "to embedding model"
            )

            # -----------------------------------------------------------------
            # 5. Generate embeddings
            # -----------------------------------------------------------------
            print(
                "\n[5/7] Generating embeddings..."
            )

            embeddings = self._embeddings.embed_documents(
                texts
            )

            print(
                "Index embedding dimension:",
                len(embeddings[0]),
            )

            print(
                f"✅ Received {len(embeddings)} embeddings"
            )

            # -----------------------------------------------------------------
            # 6. Create vector points
            # -----------------------------------------------------------------
            print(
                "\n[6/7] Creating vector points..."
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

            vector_points = (
                VectorMapper.to_vector_points(
                    embedded_chunks
                )
            )

            print(
                f"✅ Created {len(vector_points)} "
                "vector points"
            )

            # -----------------------------------------------------------------
            # Re-index cleanup
            # -----------------------------------------------------------------
            print(
                "\nPreparing re-index cleanup..."
            )

            # Delete ALL existing vectors belonging
            # to this document.
            #
            # This is intentionally based on document_id
            # rather than PostgreSQL chunk IDs so that
            # stale/orphaned Qdrant vectors are also removed.
            self._vector_provider.delete_by_filter(
                collection_name=settings.QDRANT_COLLECTION,
                filters={
                    "document_id": str(document_id),
                },
            )

            print(
                "✅ Deleted all existing vectors "
                "for document from Qdrant"
            )

            # Delete existing PostgreSQL chunks.
            existing_chunks = (
                self._chunk_repository.get_by_document_id(
                    document_id
                )
            )

            print(
                f"Existing PostgreSQL chunks: "
                f"{len(existing_chunks)}"
            )

            if existing_chunks:
                self._chunk_repository.delete_by_document_id(
                    document_id
                )

                print(
                    f"✅ Deleted {len(existing_chunks)} "
                    "old chunks from PostgreSQL"
                )

            # -----------------------------------------------------------------
            # Persist new chunks
            # -----------------------------------------------------------------
            print(
                "\nPersisting new chunks to PostgreSQL..."
            )

            chunk_records = [
                {
                    "id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "source": chunk.metadata.source,
                    "page_number": chunk.metadata.page_number,
                    "chunk_index": chunk.metadata.chunk_index,
                }
                for chunk in chunks
            ]

            self._chunk_repository.create_many(
                chunk_records
            )

            print(
                f"✅ Persisted {len(chunk_records)} "
                "chunks to PostgreSQL"
            )

            # -----------------------------------------------------------------
            # 7. Upload vectors to Qdrant
            # -----------------------------------------------------------------
            print(
                "\n[7/7] Uploading vectors to Qdrant..."
            )

            self._vector_provider.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=vector_points,
            )

            print(
                "✅ Successfully uploaded vectors"
            )

            # -----------------------------------------------------------------
            # Update document status
            # -----------------------------------------------------------------
            print(
                "\nUpdating document status..."
            )

            self._repository.update_status(
                document_id,
                DocumentStatus.INDEXED,
            )

            elapsed = time.time() - start_time

            print(
                "\n" + "=" * 80
            )
            print(
                "🎉 INDEXING COMPLETED SUCCESSFULLY"
            )
            print(
                f"Document ID : {document_id}"
            )
            print(
                f"Chunks      : {len(chunks)}"
            )
            print(
                f"Vectors     : {len(vector_points)}"
            )
            print(
                f"Time Taken  : {elapsed:.2f} seconds"
            )
            print(
                "=" * 80
            )

        except Exception as e:

            print(
                "\n" + "=" * 80
            )
            print(
                "❌ INDEXING FAILED"
            )
            print(
                "=" * 80
            )

            print(
                f"Document ID : {document_id}"
            )

            print(
                f"Error Type  : {type(e).__name__}"
            )

            print(
                f"Error       : {e}"
            )

            print(
                "\nFull traceback:\n"
            )

            traceback.print_exc()

            print(
                "=" * 80
            )

            self._repository.update_status(
                document_id,
                DocumentStatus.FAILED,
            )

            raise