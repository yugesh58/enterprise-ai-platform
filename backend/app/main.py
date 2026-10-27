
from fastapi import FastAPI
from app.api.middleware import RequestContextMiddleware

from app.api.chat import router as chat_router
from app.api.routes.document import router as document_router
from app.api.routes.health import router as health_router
from app.api.exception_handlers import register_exception_handlers
from app.api.routes.usage_analytics import router as usage_analytics_router
from app.api.routes.metrics import router as metrics_router
app = FastAPI()

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(document_router)
app.add_middleware(RequestContextMiddleware)
register_exception_handlers(app)
app.include_router(usage_analytics_router)
app.include_router(metrics_router)


@app.get("/")
def home():
    return {"message": "Enterprise AI Platform Running"}
