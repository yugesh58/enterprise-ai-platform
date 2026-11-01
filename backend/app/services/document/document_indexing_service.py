
import time
import traceback
from uuid import UUID
from app.services.document.document_index_lock import document_index_lock
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
        """Index a document while holding its distributed Redis lock."""

        with document_index_lock(document_id):
            self._index_document(document_id)
    def _index_document(
        self,
        document_id: UUID,
    ) -> None:
        """
        Process a document and safely replace its existing index.

        New vectors are uploaded before PostgreSQL chunks are replaced.
        If PostgreSQL replacement fails, newly uploaded vectors are
        removed as a compensating action.

        PostgreSQL and Qdrant do not support a shared atomic transaction.
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
            print("\n[1/8] Reading document from storage...")

            pdf_bytes = self._storage.read(
                document["storage_path"]
            )

            print(f"✅ Read {len(pdf_bytes):,} bytes")

            # -----------------------------------------------------------------
            # 2. Extract document content
            # -----------------------------------------------------------------
            print("\n[2/8] Extracting document...")

            pdf = self._pdf_processing_service.extract_document(
                pdf_bytes,
                filename=document["filename"],
            )

            print(f"✅ Pages extracted: {len(pdf.pages)}")

            # -----------------------------------------------------------------
            # 3. Generate chunks
            # -----------------------------------------------------------------
            print("\n[3/8] Creating chunks...")

            chunks = self._chunking_service.chunk_document(
                document_id=document_id,
                source=document["filename"],
                pdf=pdf,
            )

            print(f"✅ Generated {len(chunks)} chunks")

            # Capture existing PostgreSQL chunk IDs before changing
            # either PostgreSQL or Qdrant.
            existing_chunk_ids = (
                self._chunk_repository.get_ids_by_document_id(
                    document_id
                )
            )

            existing_vector_ids = [
                str(chunk_id)
                for chunk_id in existing_chunk_ids
            ]

            # -----------------------------------------------------------------
            # Handle empty documents
            # -----------------------------------------------------------------
            if not chunks:
                print(
                    "⚠️ No chunks generated. "
                    "Clearing existing PostgreSQL chunks."
                )

                # Remove existing PostgreSQL chunks transactionally.
                self._chunk_repository.replace_by_document_id(
                    document_id,
                    [],
                )

                # Remove corresponding old Qdrant vectors.
                try:
                    self._vector_provider.delete(
                        collection_name=settings.QDRANT_COLLECTION,
                        point_ids=existing_vector_ids,
                    )

                    print("✅ Existing vectors cleaned up")

                except Exception as cleanup_error:
                    # PostgreSQL replacement has already succeeded.
                    # Keep the document indexed and log cleanup failure.
                    print(
                        "⚠️ Old vector cleanup failed. "
                        f"Retry required: {cleanup_error}"
                    )

                self._repository.update_status(
                    document_id,
                    DocumentStatus.INDEXED,
                )

                print("✅ Empty document indexing completed")
                return

            # -----------------------------------------------------------------
            # 4. Prepare embedding input
            # -----------------------------------------------------------------
            print("\n[4/8] Preparing embedding input...")

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
            print("\n[5/8] Generating embeddings...")

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
            print("\n[6/8] Creating vector points...")

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

            print(
                f"✅ Created {len(vector_points)} vector points"
            )

            # Prepare PostgreSQL records.
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

            # VectorMapper assigns each point the string form
            # of its corresponding chunk UUID.
            new_vector_ids = [
                str(point.id)
                for point in vector_points
            ]

            # -----------------------------------------------------------------
            # 7. Upload new vectors and replace PostgreSQL chunks
            # -----------------------------------------------------------------
            print("\n[7/8] Uploading replacement vectors to Qdrant...")

            try:
                self._vector_provider.upsert(
                    collection_name=settings.QDRANT_COLLECTION,
                    points=vector_points,
                )

                print("✅ New vectors uploaded successfully")

                # Replace old chunks and insert new chunks in one
                # PostgreSQL transaction.
                self._chunk_repository.replace_by_document_id(
                    document_id,
                    chunk_records,
                )

                print(
                    f"✅ Replaced PostgreSQL chunks: "
                    f"{len(chunk_records)}"
                )

            except Exception:
                # If Qdrant partially uploaded vectors or PostgreSQL
                # replacement failed, attempt to remove the new vectors.
                try:
                    self._vector_provider.delete(
                        collection_name=settings.QDRANT_COLLECTION,
                        point_ids=new_vector_ids,
                    )

                    print(
                        "✅ Compensating cleanup of new vectors completed"
                    )

                except Exception as cleanup_error:
                    print(
                        "❌ New vector compensation failed: "
                        f"{cleanup_error}"
                    )

                raise

            # -----------------------------------------------------------------
            # 8. Remove old vectors
            # -----------------------------------------------------------------
            print("\n[8/8] Cleaning up old Qdrant vectors...")

            try:
                self._vector_provider.delete(
                    collection_name=settings.QDRANT_COLLECTION,
                    point_ids=existing_vector_ids,
                )

                print("✅ Old vectors cleaned up")

            except Exception as cleanup_error:
                # New PostgreSQL chunks and Qdrant vectors are already
                # committed/available. Do not mark indexing as failed
                # because cleanup of obsolete vectors failed.
                print(
                    "⚠️ Old vector cleanup failed. "
                    f"Retry/manual cleanup required: {cleanup_error}"
                )

            # -----------------------------------------------------------------
            # Update document status
            # -----------------------------------------------------------------
            print("\nUpdating document status...")

            self._repository.update_status(
                document_id,
                DocumentStatus.INDEXED,
            )

            elapsed = time.time() - start_time

            print("\n" + "=" * 80)
            print("🎉 INDEXING COMPLETED SUCCESSFULLY")
            print(f"Document ID : {document_id}")
            print(f"Chunks      : {len(chunks)}")
            print(f"Vectors     : {len(vector_points)}")
            print(f"Time Taken  : {elapsed:.2f} seconds")
            print("=" * 80)

        except Exception as e:
            print("\n" + "=" * 80)
            print("❌ INDEXING FAILED")
            print("=" * 80)

            print(f"Document ID : {document_id}")
            print(f"Error Type  : {type(e).__name__}")
            print(f"Error       : {e}")

            print("\nFull traceback:\n")
            traceback.print_exc()

            print("=" * 80)

            self._repository.update_status(
                document_id,
                DocumentStatus.FAILED,
            )

            raise
