from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.config import settings
from app.core.database import get_connection
from app.repositories.document_repository import DocumentRepository
from app.services.document.document_service import DocumentService
from app.storage.file_storage.providers.local_storage_provider import (
    LocalStorageProvider,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


def get_document_service() -> DocumentService:
    """
    Create and return a DocumentService instance.
    """

    with get_connection() as connection:

        repository = DocumentRepository(connection)

        storage = LocalStorageProvider(
            Path(settings.UPLOAD_DIRECTORY)
        )

        yield DocumentService(
            repository=repository,
            storage=storage,
        )


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
):
    """
    Upload a document and persist its metadata.
    """

    try:
        content = await file.read()

        document_id = service.upload_document(
            filename=file.filename,
            content_type=file.content_type,
            content=content,
        )

        return {
            "document_id": str(document_id),
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "message": "Document uploaded successfully.",
        }

    except ValueError as ex:
        raise HTTPException(
            status_code=400,
            detail=str(ex),
        )

    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Document upload failed: {str(ex)}",
        )