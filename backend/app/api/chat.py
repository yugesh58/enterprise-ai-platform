from fastapi import APIRouter

from app.agents.agent_dispatcher import dispatch_agent
from app.schemas.agent_request import AgentRequest
from app.schemas.chat import ChatRequest
from app.services.router import route_question

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):

    # User question
    question = request.question

    # Decide which agent to use
    selected_agent = route_question(question)

    # Build the AgentRequest
    agent_request = AgentRequest(question=question)

    # Execute the agent
    response = dispatch_agent(
        selected_agent,
        agent_request,
    )

    return {
        "selected_agent": selected_agent,
        "answer": response.answer,
        "status": response.status,
        "message": response.message,
        "data": response.data,
        "chart": response.chart,
        "citations": response.citations,
        "metadata": response.metadata,
    }
