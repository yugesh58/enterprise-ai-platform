
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies.document import (
    get_document_service,
    get_document_indexing_service,
    get_document_search_service,
    get_document_chat_service,
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def document_service():
    return Mock()


@pytest.fixture
def indexing_service():
    return Mock()


@pytest.fixture
def search_service():
    return Mock()


@pytest.fixture
def chat_service():
    return Mock()


def test_upload_new_document_returns_202_and_schedules_indexing(
    client,
    document_service,
    indexing_service,
):
    document_id = uuid4()

    document_service.upload_document.return_value = {
        "document_id": document_id,
        "status": "PROCESSING",
        "is_existing": False,
        "should_index": True,
    }

    app.dependency_overrides[get_document_service] = (
        lambda: document_service
    )
    app.dependency_overrides[get_document_indexing_service] = (
        lambda: indexing_service
    )

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "test.txt",
                b"Enterprise AI document content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 202
    body = response.json()

    assert body["document_id"] == str(document_id)
    assert body["filename"] == "test.txt"
    assert body["content_type"] == "text/plain"
    assert body["size"] == len(b"Enterprise AI document content")
    assert body["status"] == "PROCESSING"
    assert body["existing_document"] is False

    document_service.upload_document.assert_called_once_with(
        filename="test.txt",
        content_type="text/plain",
        content=b"Enterprise AI document content",
    )

    # BackgroundTasks are executed by TestClient before the request finishes.
    indexing_service.index_document.assert_called_once_with(document_id)


def test_upload_existing_indexed_document_does_not_reindex(
    client,
    document_service,
    indexing_service,
):
    document_id = uuid4()

    document_service.upload_document.return_value = {
        "document_id": document_id,
        "status": "INDEXED",
        "is_existing": True,
        "should_index": False,
    }

    app.dependency_overrides[get_document_service] = (
        lambda: document_service
    )
    app.dependency_overrides[get_document_indexing_service] = (
        lambda: indexing_service
    )

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "existing.txt",
                b"Existing content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 202
    assert response.json()["existing_document"] is True
    assert "no new indexing required" in response.json()["message"]

    indexing_service.index_document.assert_not_called()



def test_upload_value_error_returns_400(
    client,
    document_service,
    indexing_service,
):
    document_service.upload_document.side_effect = ValueError(
        "Document content cannot be empty."
    )

    app.dependency_overrides[get_document_service] = (
        lambda: document_service
    )
    app.dependency_overrides[get_document_indexing_service] = (
        lambda: indexing_service
    )

    response = client.post(
        "/documents/upload",
        files={
            "file": ("empty.txt", b"", "text/plain")
        },
    )

    assert response.status_code == 400

    body = response.json()
    assert body["error"]["code"] == "HTTP_ERROR"
    assert body["error"]["message"] == (
        "Document content cannot be empty."
    )
    assert body["error"]["request_id"] == (
        response.headers["x-request-id"]
    )

    indexing_service.index_document.assert_not_called()


def test_search_documents_passes_request_to_service(
    client,
    search_service,
):
    document_id = str(uuid4())
    expected_results = [
        {
            "text": "Enterprise AI uses a Document Agent.",
            "score": 0.92,
            "source": "guide.pdf",
            "page_number": 1,
        }
    ]
    search_service.search.return_value = expected_results

    app.dependency_overrides[get_document_search_service] = (
        lambda: search_service
    )

    response = client.post(
        "/documents/search",
        json={
            "query": "What does the Document Agent do?",
            "top_k": 3,
            "document_id": document_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["query"] == (
        "What does the Document Agent do?"
    )
    assert response.json()["results"] == expected_results

    search_service.search.assert_called_once_with(
        query="What does the Document Agent do?",
        top_k=3,
        document_id=document_id,
    )


def test_document_chat_returns_answer_and_sources(
    client,
    chat_service,
):
    expected_response = {
        "answer": "The Document Agent retrieves relevant document chunks.",
        "sources": [
            {
                "source": "guide.pdf",
                "page_number": 1,
                "score": 0.92,
                "text": "The Document Agent retrieves relevant chunks.",
            }
        ],
    }
    chat_service.chat.return_value = expected_response

    app.dependency_overrides[get_document_chat_service] = (
        lambda: chat_service
    )

    document_id = str(uuid4())

    response = client.post(
        "/documents/chat",
        json={
            "question": "What does the Document Agent do?",
            "top_k": 4,
            "document_id": document_id,
        },
    )

    assert response.status_code == 200
    assert response.json() == expected_response

    chat_service.chat.assert_called_once_with(
        question="What does the Document Agent do?",
        top_k=4,
        document_id=document_id,
    )


def test_document_chat_rejects_missing_question(
    client,
    chat_service,
):
    app.dependency_overrides[get_document_chat_service] = (
        lambda: chat_service
    )

    response = client.post(
        "/documents/chat",
        json={"top_k": 4},
    )

    assert response.status_code == 422
    chat_service.chat.assert_not_called()
    id="80426"