
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from app.ai.providers.usage_analytics import (
    get_daily_usage,
    get_request_usage,
)

router = APIRouter(
    prefix="/analytics/llm-usage",
    tags=["LLM Usage Analytics"],
)


class RequestUsageItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    request_id: UUID
    operation: str
    provider: str
    model: str
    total_calls: int
    failed_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_estimated_cost_usd: Decimal
    total_duration_ms: Decimal
    error_types: list[str]


class DailyUsageItem(BaseModel):
    usage_date: date
    provider: str
    model: str
    total_calls: int
    failed_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_estimated_cost_usd: Decimal
    error_types: list[str]


@router.get("/requests/{request_id}", response_model=list[RequestUsageItem])
def request_usage(request_id: UUID):
    """Return aggregated LLM usage for a request."""
    return get_request_usage(str(request_id))


@router.get("/daily", response_model=list[DailyUsageItem])
def daily_usage(
    days: int = Query(default=7, ge=1, le=365),
):
    """Return daily usage grouped by provider and model."""
    return get_daily_usage(days=days)