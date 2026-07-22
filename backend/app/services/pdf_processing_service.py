from pathlib import Path

import fitz

from app.schemas.pdf_processing import (
    PDFMetadata,
    PageContent,
    PDFProcessingResult,
)


class PDFProcessingService:
    """Service responsible for extracting information from PDF documents."""

    def extract_document(
        self,
        file_path: str | Path,
    ) -> PDFProcessingResult:
        """
        Extract metadata and page-wise text from a PDF.
        """

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        if file_path.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported.")

        with fitz.open(file_path) as document:
            return PDFProcessingResult(
                page_count=document.page_count,
                metadata=self._extract_metadata(document),
                pages=self._extract_pages(document),
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
        pages: list[PageContent] = []

        for page_number, page in enumerate(document, start=1):
            pages.append(
                PageContent(
                    page_number=page_number,
                    text=page.get_text(),
                )
            )

        return pages