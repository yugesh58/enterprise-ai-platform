from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.dependencies.security import require_api_key

router = APIRouter(
    tags=["Metrics"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )