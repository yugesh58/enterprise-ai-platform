from collections.abc import Iterator
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents.agent_dispatcher import dispatch_agent
from app.agents.rag_agent import RAGAgent
from app.schemas.agent_request import AgentRequest
from app.schemas.chat import ChatRequest
from app.services.router import route_question
from app.storage.memory.factory import get_memory_provider


router = APIRouter()

memory = get_memory_provider()


@router.post("/chat")
async def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        return {
            "selected_agent": None,
            "answer": "",
            "status": "failed",
            "message": "Question cannot be empty.",
            "data": None,
            "chart": None,
            "citations": [],
            "metadata": {},
        }

    conversation_id = request.conversation_id or str(uuid4())

    chat_history = memory.get_history(
        conversation_id=conversation_id,
        limit=10,
    )

    memory.add_message(
        conversation_id=conversation_id,
        role="user",
        content=question,
    )

    selected_agent = route_question(question)

    agent_request = AgentRequest(
        question=question,
        chat_history=chat_history,
    )

    response = dispatch_agent(
        selected_agent,
        agent_request,
    )

    if response.answer:
        memory.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response.answer,
        )

    return {
        "conversation_id": conversation_id,
        "selected_agent": selected_agent,
        "answer": response.answer,
        "status": response.status,
        "message": response.message,
        "data": response.data,
        "chart": response.chart,
        "citations": response.citations,
        "metadata": response.metadata,
    }


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    question = request.question.strip()

    if not question:
        return StreamingResponse(
            iter(["Question cannot be empty."]),
            media_type="text/plain",
            status_code=400,
        )

    conversation_id = request.conversation_id or str(uuid4())

    chat_history = memory.get_history(
        conversation_id=conversation_id,
        limit=10,
    )

    memory.add_message(
        conversation_id=conversation_id,
        role="user",
        content=question,
    )

    selected_agent = route_question(question)

    agent_request = AgentRequest(
        question=question,
        chat_history=chat_history,
    )

    def generate() -> Iterator[str]:
        """
        Generate and stream the assistant response.
        """

        full_response = ""

        try:
            if selected_agent == "rag":
                agent = RAGAgent()

                for chunk in agent.stream(agent_request):
                    full_response += chunk
                    yield chunk

            else:
                yield (
                    "Streaming is currently supported "
                    "for the RAG agent only."
                )
                return

            if full_response:
                memory.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                )

        except Exception as exc:
            yield f"\n[ERROR] {str(exc)}"

    response = StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )

    response.headers["X-Conversation-ID"] = conversation_id
    response.headers["X-Agent"] = selected_agent
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"

    return response