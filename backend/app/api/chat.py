from collections.abc import Iterator
from uuid import uuid4
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents.agent_dispatcher import dispatch_agent
from app.agents.rag_agent import RAGAgent
from app.schemas.agent_request import AgentRequest
from app.schemas.chat import ChatRequest
from app.services.router import route_question
from app.storage.memory.factory import get_memory_provider
from app.core.request_context import RequestContext


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
    context=RequestContext(
        conversation_id=conversation_id,
        selected_agent=selected_agent,
    ),
    chat_history=chat_history,
    attributes={
        "conversation_id": conversation_id,
    },
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

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    question = request.question.strip()

    def encode_event(event: str, payload: dict) -> str:
        data = json.dumps(payload, ensure_ascii=False)
        return f"event: {event}\ndata: {data}\n\n"

    if not question:
        return StreamingResponse(
            iter([
                encode_event(
                    "error",
                    {"message": "Question cannot be empty."},
                )
            ]),
            media_type="text/event-stream",
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
        context=RequestContext(
            conversation_id=conversation_id,
            selected_agent=selected_agent,
        ),
        chat_history=chat_history,
        attributes={"conversation_id": conversation_id},
    )

    def generate() -> Iterator[str]:
        full_response = ""

        try:
            if selected_agent != "rag":
                message = (
                    "Streaming is currently supported "
                    "for the RAG agent only."
                )
                full_response = message

                yield encode_event(
                    "message",
                    {"message": message},
                )
            else:
                agent = RAGAgent()

                for chunk in agent.stream(agent_request):
                    if not chunk:
                        continue

                    full_response += chunk

                    yield encode_event(
                        "chunk",
                        {"chunk": chunk},
                    )

            if full_response:
                memory.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                )

            yield encode_event(
                "done",
                {"conversation_id": conversation_id},
            )

        except Exception:
            # Never expose internal exception details to clients.
            yield encode_event(
                "error",
                {
                    "message": (
                        "An error occurred while streaming "
                        "the response."
                    )
                },
            )

    response = StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )

    response.headers["X-Conversation-ID"] = conversation_id
    response.headers["X-Agent"] = str(selected_agent)
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"

    return response
