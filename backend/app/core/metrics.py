from prometheus_client import Counter, Histogram


# HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of completed HTTP requests.",
    labelnames=("method", "route", "status_code"),
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    labelnames=("method", "route"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)


# LLM request metrics
LLM_REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total number of LLM requests.",
    labelnames=("provider", "model", "operation", "outcome", "error_type"),
)

LLM_REQUEST_DURATION_SECONDS = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds.",
    labelnames=("provider", "model", "operation", "outcome"),
    buckets=(
        0.1, 0.25, 0.5, 1.0, 2.5, 5.0,
        10.0, 15.0, 30.0, 60.0, 120.0,
    ),
)

LLM_TOKENS_TOTAL = Counter(
    "llm_tokens_total",
    "Total number of LLM tokens consumed.",
    labelnames=("provider", "model", "token_type"),
)

LLM_ESTIMATED_COST_USD_TOTAL = Counter(
    "llm_estimated_cost_usd_total",
    "Estimated cumulative LLM cost in USD.",
    labelnames=("provider", "model"),
)