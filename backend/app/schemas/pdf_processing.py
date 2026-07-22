from pydantic import BaseModel, Field


class PDFMetadata(BaseModel):
    """Metadata extracted from a PDF."""

    title: str = ""
    author: str = ""
    subject: str = ""
    keywords: str = ""
    creator: str = ""
    producer: str = ""
    creation_date: str = Field(default="", alias="creationDate")
    modification_date: str = Field(default="", alias="modDate")


class PageContent(BaseModel):
    """Represents a single page of a PDF."""

    page_number: int
    text: str


class PDFProcessingResult(BaseModel):
    """Complete result of PDF extraction."""

    page_count: int
    metadata: PDFMetadata
    pages: list[PageContent]