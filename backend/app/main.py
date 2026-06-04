from fastapi import FastAPI
from app.api.chat import router as chat_router
from app.api.sql_agent import router as sql_router

app = FastAPI()

app.include_router(chat_router)
app.include_router(sql_router)


@app.get("/")
def home():
    return {"message": "Enterprise AI Platform Running"}