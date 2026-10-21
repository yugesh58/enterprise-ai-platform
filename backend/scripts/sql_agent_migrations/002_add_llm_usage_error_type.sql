
ALTER TABLE llm_usage_events
ADD COLUMN IF NOT EXISTS error_type VARCHAR(50);
