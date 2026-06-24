from fastapi import APIRouter

from app.agents.agent_dispatcher import dispatch_agent
from app.services.router import route_question
from app.models.chat_request import chatRequest

router = APIRouter()

@router.post("/chat")
async def chat(request:chatRequest):
    question="Which region has highest sales"
    question=request.question
    selected_agent=route_question(question)

    response = dispatch_agent(selected_agent,question)
    selected_agent = route_question(question)

    print(f"Selected Agent: '{selected_agent}'")
    print(f"Length: {len(selected_agent)}")

    return {
        "selected_agent":selected_agent,
        "response": response
    }
