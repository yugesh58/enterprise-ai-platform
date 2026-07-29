from uuid import UUID, uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.schemas.chunk import ChunkMetadata, DocumentChunk
from app.schemas.pdf_processing import PDFProcessingResult


class ChunkingService:
    """
    Service responsible for creating searchable chunks from
    extracted PDF text.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def chunk_document(
        self,
        document_id: UUID,
        source: str,
        pdf: PDFProcessingResult,
    ) -> list[DocumentChunk]:
        """
        Split an extracted PDF into searchable chunks.
        """

        chunks: list[DocumentChunk] = []

        chunk_index = 0

        for page in pdf.pages:

            cleaned_text = self._clean_text(page.text)

            if not cleaned_text:
                continue

            split_text = self.splitter.split_text(cleaned_text)

            for text in split_text:

                chunks.append(
                    DocumentChunk(
                        chunk_id=uuid4(),          # ✅ Generate a valid UUID
                        document_id=document_id,
                        text=text,
                        metadata=ChunkMetadata(
                            source=source,
                            page_number=page.page_number,
                            chunk_index=chunk_index,
                        ),
                    )
                )

                chunk_index += 1

        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Basic text normalization before chunking.
        """

        if not text:
            return ""

        lines = []

        for line in text.splitlines():

            line = line.strip()

            if line:
                lines.append(line)

        return "\n".join(lines)