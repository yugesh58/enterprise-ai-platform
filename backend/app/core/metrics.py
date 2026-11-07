from prometheus_client import Counter, Histogram
from prometheus_client import Gauge

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
# Agent execution metrics
AGENT_EXECUTIONS_TOTAL = Counter(
    "agent_executions_total",
    "Total number of agent executions.",
    labelnames=("agent", "operation", "outcome"),
)

AGENT_EXECUTION_DURATION_SECONDS = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration in seconds.",
    labelnames=("agent", "operation"),
    buckets=(
        0.01, 0.05, 0.1, 0.25, 0.5,
        1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0,
    ),
)
# Infrastructure dependency health
DEPENDENCY_HEALTH = Gauge(
    "dependency_health",
    "Latest readiness status of infrastructure dependencies (1=healthy, 0=unhealthy).",
    labelnames=("dependency",),
)