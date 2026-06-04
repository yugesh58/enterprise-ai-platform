from fastapi import APIRouter
from app.graphs.sql_graph import sql_graph
from app.memory.conversation_memory import get_memory

router = APIRouter()


@router.get("/ask")
async def ask_database(question: str):
    result=sql_graph.invoke({
        "question":question,
        "retry_count":0
    })    

    return result

@router.get("/memory")
async def view_memory():

    return {
        "memory": get_memory()
    }