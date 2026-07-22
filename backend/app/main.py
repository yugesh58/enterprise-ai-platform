from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.routes.document import router as document_router


app = FastAPI()

app.include_router(chat_router)
app.include_router(document_router)


@app.get("/")
def home():
    return {"message": "Enterprise AI Platform Running"}
