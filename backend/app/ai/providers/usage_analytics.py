
from sqlalchemy import text

from app.storage.database.connection import sql_engine


def get_request_usage(request_id: str) -> list[dict]:
    """Return LLM usage totals grouped by operation for one request."""
    query = text("""
        SELECT
            request_id,
            operation,
            provider,
            model,
            COUNT(*) AS total_calls,
            COUNT(*) FILTER (WHERE outcome = 'failure') AS failed_calls,
            COALESCE(SUM(input_tokens), 0) AS total_input_tokens,
            COALESCE(SUM(output_tokens), 0) AS total_output_tokens,
            COALESCE(SUM(estimated_cost_usd), 0)
                AS total_estimated_cost_usd,
            ROUND(COALESCE(SUM(duration_ms), 0), 2)
                AS total_duration_ms
        FROM llm_usage_events
        WHERE request_id = :request_id
        GROUP BY request_id, operation, provider, model
        ORDER BY total_estimated_cost_usd DESC
    """)

    with sql_engine.connect() as connection:
        rows = connection.execute(
            query,
            {"request_id": request_id},
        ).mappings().all()

    return [dict(row) for row in rows]


def get_daily_usage(days: int = 7) -> list[dict]:
    """Return daily LLM usage grouped by provider and model."""
    if days < 1 or days > 365:
        raise ValueError("days must be between 1 and 365")

    query = text("""
        SELECT
            DATE(created_at AT TIME ZONE 'UTC') AS usage_date,
            provider,
            model,
            COUNT(*) AS total_calls,
            COUNT(*) FILTER (WHERE outcome = 'failure') AS failed_calls,
            COALESCE(SUM(input_tokens), 0) AS total_input_tokens,
            COALESCE(SUM(output_tokens), 0) AS total_output_tokens,
            COALESCE(SUM(estimated_cost_usd), 0)
                AS total_estimated_cost_usd
        FROM llm_usage_events
        WHERE created_at >= NOW() - (:days * INTERVAL '1 day')
        GROUP BY 1, provider, model
        ORDER BY usage_date DESC, total_estimated_cost_usd DESC
    """)

    with sql_engine.connect() as connection:
        rows = connection.execute(
            query,
            {"days": days},
        ).mappings().all()

    return [dict(row) for row in rows]
