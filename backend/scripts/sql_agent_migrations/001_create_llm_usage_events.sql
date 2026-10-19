CREATE TABLE IF NOT EXISTS llm_usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    request_id VARCHAR(100),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(150) NOT NULL,
    operation VARCHAR(30) NOT NULL,

    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,

    estimated_cost_usd NUMERIC(18, 10),
    duration_ms NUMERIC(12, 2) NOT NULL,
    outcome VARCHAR(20) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_llm_usage_events_created_at
    ON llm_usage_events (created_at);

CREATE INDEX IF NOT EXISTS ix_llm_usage_events_request_id
    ON llm_usage_events (request_id);

CREATE INDEX IF NOT EXISTS ix_llm_usage_events_provider_model
    ON llm_usage_events (provider, model);