from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)
from app.services.document.document_chat_service import (
    DocumentChatService,
)
from app.services.document.document_search_service import (
    DocumentSearchService,
)

from app.api.dependencies.document import (
    get_document_indexing_service,
    get_document_search_service,
    get_document_service,
    get_document_chat_service,
)

from app.schemas.search import SearchRequest

from app.enums.document_status import DocumentStatus
from app.services.document.document_indexing_service import (
    DocumentIndexingService,
)
from app.services.document.document_service import (
    DocumentService,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post("/upload", status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
    indexing_service: DocumentIndexingService = Depends(
        get_document_indexing_service
    ),  
    ):
    try:
        content = await file.read()

        result = document_service.upload_document(
            filename=file.filename,
            content_type=file.content_type,
            content=content,
        )

        document_id = result["document_id"]
        status = result["status"]

        if result["should_index"]:
            background_tasks.add_task(
                indexing_service.index_document,
                document_id,
            )

        if result["is_existing"] and not result["should_index"]:
            message = "Existing document reused; no new indexing required."
        elif result["is_existing"]:
            message = "Existing failed document queued for re-indexing."
        else:
            message = "Document uploaded successfully. Indexing has started."

        return {
            "document_id": str(document_id),
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "status": status,
            "existing_document": result["is_existing"],
            "message": message,
        }

    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

    
    except Exception:
        
        logger.exception("Document upload failed")

        raise HTTPException(
            status_code=500,
            detail="Document upload failed. Please try again.",
        )

@router.post("/search")
def search_documents(
    request: SearchRequest,
    search_service: DocumentSearchService = Depends(
        get_document_search_service
    ),
):
    results = search_service.search(
        query=request.query,
        top_k=request.top_k,
        document_id=request.document_id,
    )

    return {
        "query": request.query,
        "results": results,
    }

@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    chat_service: DocumentChatService = Depends(
        get_document_chat_service,
    ),
):

    return chat_service.chat(
        question=request.question,
        top_k=request.top_k,
        document_id=request.document_id,
    )