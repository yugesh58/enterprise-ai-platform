
from fastapi import FastAPI
from app.api.middleware import RequestContextMiddleware

from app.api.chat import router as chat_router
from app.api.routes.document import router as document_router
from app.api.routes.health import router as health_router

app = FastAPI()

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(document_router)
app.add_middleware(RequestContextMiddleware)


@app.get("/")
def home():
    return {"message": "Enterprise AI Platform Running"}
