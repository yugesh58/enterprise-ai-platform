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

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    status_code=202,
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(
        get_document_service
    ),
    indexing_service: DocumentIndexingService = Depends(
        get_document_indexing_service
    ),
):
    """
    Upload a document and start indexing it in the background.

    The endpoint immediately returns once the document has been
    persisted. PDF extraction, chunking, embedding generation and
    vector indexing continue asynchronously.
    """

    try:
        content = await file.read()

        document_id = document_service.upload_document(
            filename=file.filename,
            content_type=file.content_type,
            content=content,
        )

        background_tasks.add_task(
            indexing_service.index_document,
            document_id,
        )

        return {
            "document_id": str(document_id),
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "status": DocumentStatus.PROCESSING.value,
            "message": (
                "Document uploaded successfully. "
                "Indexing has started."
            ),
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
    )