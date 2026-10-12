
from pathlib import Path

import fitz

from app.schemas.pdf_processing import (
    PDFMetadata,
    PageContent,
    PDFProcessingResult,
)


class PDFProcessingService:
    """Extract text and metadata from supported document formats."""

    def extract_document(
        self,
        file_bytes: bytes,
        filename: str | None = None,
    ) -> PDFProcessingResult:
        """Extract page-wise text from PDF or plain-text files."""

        if not file_bytes:
            raise ValueError("Document content cannot be empty.")

        extension = Path(filename or "").suffix.lower()

        if extension == ".txt":
            text = file_bytes.decode("utf-8-sig")

            return PDFProcessingResult(
                page_count=1,
                metadata=PDFMetadata(),
                pages=[
                    PageContent(
                        page_number=1,
                        text=text,
                    )
                ],
            )

        if extension == ".pdf" or not extension:
            with fitz.open(
                stream=file_bytes,
                filetype="pdf",
            ) as document:
                return PDFProcessingResult(
                    page_count=document.page_count,
                    metadata=self._extract_metadata(document),
                    pages=self._extract_pages(document),
                )

        raise ValueError(
            f"Unsupported document format: {extension}"
        )

    def _extract_metadata(
        self,
        document: fitz.Document,
    ) -> PDFMetadata:
        metadata = document.metadata or {}

        return PDFMetadata(
            title=metadata.get("title", "") or "",
            author=metadata.get("author", "") or "",
            subject=metadata.get("subject", "") or "",
            keywords=metadata.get("keywords", "") or "",
            creator=metadata.get("creator", "") or "",
            producer=metadata.get("producer", "") or "",
            creationDate=metadata.get("creationDate", "") or "",
            modDate=metadata.get("modDate", "") or "",
        )

    def _extract_pages(
        self,
        document: fitz.Document,
    ) -> list[PageContent]:
        return [
            PageContent(
                page_number=page_number,
                text=page.get_text(),
            )
            for page_number, page in enumerate(document, start=1)
        ]
