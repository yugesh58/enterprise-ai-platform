import time
import traceback
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
        Process a document and index it into the vector database.
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
            print("\n[1/7] Reading document from storage...")
            pdf_bytes = self._storage.read(document["storage_path"])
            print(f"✅ Read {len(pdf_bytes):,} bytes")

            # -----------------------------------------------------------------
            print("\n[2/7] Extracting PDF...")
            pdf = self._pdf_processing_service.extract_document(pdf_bytes)

            print(f"✅ Pages extracted: {len(pdf.pages)}")

            # -----------------------------------------------------------------
            print("\n[3/7] Creating chunks...")
            chunks = self._chunking_service.chunk_document(
                document_id=document_id,
                source=document["filename"],
                pdf=pdf,
            )

            print(f"✅ Generated {len(chunks)} chunks")

            if not chunks:
                print("⚠️ No chunks generated.")

                self._repository.update_status(
                    document_id,
                    DocumentStatus.INDEXED,
                )

                return

            # -----------------------------------------------------------------
            print("\n[4/7] Preparing text for embeddings...")

            texts = [chunk.text for chunk in chunks]

            print(f"✅ Sending {len(texts)} chunks to embedding model")

            # -----------------------------------------------------------------
            print("\n[5/7] Generating embeddings...")

            embeddings = self._embeddings.embed_documents(texts)
            print("Index embedding dimension:", len(embeddings[0]))

            print(f"✅ Received {len(embeddings)} embeddings")

            # -----------------------------------------------------------------
            print("\n[6/7] Creating vector points...")

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

            print(f"✅ Created {len(vector_points)} vector points")

            # -----------------------------------------------------------------
            print("\n[7/7] Uploading vectors to Qdrant...")

            self._vector_provider.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=vector_points,
            )

            print("✅ Successfully uploaded vectors")

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