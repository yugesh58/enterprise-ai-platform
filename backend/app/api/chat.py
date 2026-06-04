from fastapi import APIRouter
from app.services.llm import llm

router = APIRouter()

@router.get("/chat")
async def chat():

    response = llm.invoke("Say hello like an AI engineer")

    return {
        "response": response.content
    }