
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
import pytest
from app.api.dependencies.document import get_vector_provider
from app.api.dependencies.rate_limit import enforce_rate_limit
from app.api.dependencies.repositories import (
    get_document_chunk_repository,
    get_document_repository,
)
from app.api.dependencies.storage import get_storage_provider
from app.core.config import settings
from app.enums.document_status import DocumentStatus
from app.main import app


class FakeStorage:
    def __init__(self):
        self.files = {}

    def save(self, filename: str, content: bytes) -> Path:
        path = Path("/fake-storage") / f"{uuid4()}-{filename}"
        self.files[str(path)] = content
        return path

    def read(self, path: Path) -> bytes:
        return self.files[str(path)]

    def delete(self, path: Path) -> None:
        self.files.pop(str(path), None)

    def exists(self, path: Path) -> bool:
        return str(path) in self.files


class FakeDocumentRepository:
    def __init__(self):
        self.documents = {}

    def get_by_content_hash(self, content_hash):
        for document in self.documents.values():
            if document["content_hash"] == content_hash:
                return document
        return None

    def create(self, **kwargs):
        document_id = uuid4()
        self.documents[document_id] = {
            "id": document_id,
            **kwargs,
            "status": DocumentStatus.PROCESSING,
        }
        return document_id

    def get_by_id(self, document_id):
        return self.documents.get(document_id)

    def update_status(self, document_id, status):
        self.documents[document_id]["status"] = status


class FakeChunkRepository:
    def __init__(self):
        self.chunks = {}

    def get_ids_by_document_id(self, document_id):
        return [
            chunk["id"]
            for chunk in self.chunks.get(document_id, [])
        ]

    def replace_by_document_id(self, document_id, chunks):
        self.chunks[document_id] = list(chunks)

    def keyword_search(self, query, top_k=5, document_id=None):
        terms = set(query.casefold().split())
        matching = []

        for current_document_id, chunks in self.chunks.items():
            if document_id and current_document_id != document_id:
                continue

            for chunk in chunks:
                text = chunk["text"]
                matched_terms = terms.intersection(
                    set(text.casefold().split())
                )

                if matched_terms:
                    matching.append({
                        **chunk,
                        "keyword_score": float(len(matched_terms)),
                    })

        return sorted(
            matching,
            key=lambda item: item["keyword_score"],
            reverse=True,
        )[:top_k]


class FakeVectorProvider:
    def __init__(self):
        self.points = {}

    def upsert(self, collection_name, points):
        for point in points:
            self.points[str(point.id)] = point

    def search(
        self,
        collection_name,
        query_vector,
        limit=5,
        filters=None,
    ):
        results = []

        for point_id, point in self.points.items():
            payload = point.payload

            if filters:
                if any(
                    payload.get(key) != value
                    for key, value in filters.items()
                ):
                    continue

            results.append({
                "id": point_id,
                "score": 0.95,
                "payload": payload,
            })

        return results[:limit]

    def delete(self, collection_name, point_ids):
        for point_id in point_ids:
            self.points.pop(str(point_id), None)

    def connect(self):
        pass

    def create_collection(self, *args, **kwargs):
        pass

    def delete_collection(self, *args, **kwargs):
        pass

    def delete_by_filter(self, *args, **kwargs):
        pass

    def close(self):
        pass


class FakeEmbeddings:
    def embed_documents(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, query):
        return [0.1, 0.2, 0.3]

@pytest.fixture
def client():
    with TestClient(
        app,
        headers={"X-API-Key": settings.API_KEY},
    ) as test_client:
        yield test_client


@pytest.fixture
def client_without_server_exceptions():
    with TestClient(
        app,
        headers={"X-API-Key": settings.API_KEY},
        raise_server_exceptions=False,
    ) as test_client:
        yield test_client
@pytest.fixture
def document_workflow_dependencies(monkeypatch):
    from app.services.document import (
        document_chat_service,
        document_indexing_service,
        document_search_service,
    )

    from app.api.dependencies import document as document_dependencies

    documents = FakeDocumentRepository()
    chunks = FakeChunkRepository()
    storage = FakeStorage()
    vectors = FakeVectorProvider()
    embeddings = FakeEmbeddings()

    monkeypatch.setattr(
        document_indexing_service,
        "get_embeddings",
        lambda: embeddings,
    )
    monkeypatch.setattr(
        document_search_service,
        "get_embeddings",
        lambda: embeddings,
    )
    monkeypatch.setattr(
        document_dependencies,
        "get_vector_provider",
        lambda: vectors,
    )
    monkeypatch.setattr(
        document_indexing_service,
        "document_index_lock",
        lambda document_id: nullcontext(),
    )
    monkeypatch.setattr(
        document_chat_service.provider,
        "invoke",
        lambda prompt: SimpleNamespace(
            content=(
                "According to the uploaded document, "
                "employees receive 24 annual leave days."
            )
        ),
    )

    monkeypatch.setitem(
    app.dependency_overrides,
    get_document_repository,
    lambda: documents,
    )
    monkeypatch.setitem(
    app.dependency_overrides,
    get_document_chunk_repository,
    lambda: chunks,
    )
    monkeypatch.setitem(
    app.dependency_overrides,
    get_storage_provider,
    lambda: storage,
    )
    monkeypatch.setitem(
    app.dependency_overrides,
    enforce_rate_limit,
    lambda: None,
    )

    yield SimpleNamespace(
        documents=documents,
        chunks=chunks,
        storage=storage,
        vectors=vectors,
    )

    


def test_upload_index_and_chat_document_end_to_end(
    client,
    document_workflow_dependencies,
):
    content = (
        b"Company leave policy. "
        b"Employees receive 24 annual leave days each year. "
        b"Unused annual leave is subject to company policy."
    )

    # 1. Upload through the real API and DocumentService.
    upload_response = client.post(
        "/documents/upload",
        files={
            "file": (
                "leave-policy.txt",
                content,
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 202

    upload_body = upload_response.json()
    document_id = UUID(upload_body["document_id"])

    assert upload_body["filename"] == "leave-policy.txt"
    assert upload_body["status"] == "PROCESSING"
    assert upload_body["existing_document"] is False

    # TestClient executes FastAPI BackgroundTasks before returning.
    # The real indexing service should have completed by this point.
    dependencies = document_workflow_dependencies

    document = dependencies.documents.get_by_id(document_id)

    assert document is not None
    assert document["status"] == DocumentStatus.INDEXED

    indexed_chunks = dependencies.chunks.chunks[document_id]

    assert indexed_chunks
    assert any(
        "24 annual leave days" in chunk["text"]
        for chunk in indexed_chunks
    )

    assert dependencies.vectors.points

    # 2. Ask a question through the real document chat route.
    chat_response = client.post(
        "/documents/chat",
        json={
            "question": "How many annual leave days do employees receive?",
            "top_k": 5,
            "document_id": str(document_id),
        },
    )

    assert chat_response.status_code == 200

    chat_body = chat_response.json()

    assert "24 annual leave days" in chat_body["answer"]
    assert chat_body["sources"]

    source = chat_body["sources"][0]

    assert source["source"] == "leave-policy.txt"
    assert source["page_number"] == 1
    assert "24 annual leave days" in source["text"]

def test_duplicate_upload_reuses_existing_document(
    client,
    document_workflow_dependencies,
):
    content = (
        b"Company leave policy. "
        b"Employees receive 24 annual leave days each year."
    )

    first_response = client.post(
        "/documents/upload",
        files={
            "file": (
                "leave-policy.txt",
                content,
                "text/plain",
            )
        },
    )

    assert first_response.status_code == 202

    first_body = first_response.json()
    first_document_id = first_body["document_id"]

    dependencies = document_workflow_dependencies

    assert first_body["existing_document"] is False
    assert len(dependencies.documents.documents) == 1

    indexed_chunk_count = sum(
        len(chunks)
        for chunks in dependencies.chunks.chunks.values()
    )
    indexed_vector_count = len(dependencies.vectors.points)

    # Upload identical content again.
    second_response = client.post(
        "/documents/upload",
        files={
            "file": (
                "leave-policy.txt",
                content,
                "text/plain",
            )
        },
    )

    assert second_response.status_code == 202

    second_body = second_response.json()

    assert second_body["document_id"] == first_document_id
    assert second_body["existing_document"] is True
    assert second_body["message"] == (
        "Existing document reused; no new indexing required."
    )

    # Verify no duplicate document or reindexing.
    assert len(dependencies.documents.documents) == 1

    assert sum(
        len(chunks)
        for chunks in dependencies.chunks.chunks.values()
    ) == indexed_chunk_count

    assert len(dependencies.vectors.points) == indexed_vector_count
def test_invalid_document_upload_is_rejected(
    client,
    document_workflow_dependencies,
):
    dependencies = document_workflow_dependencies

    # Unsupported extension
    unsupported_response = client.post(
        "/documents/upload",
        files={
            "file": (
                "malware.exe",
                b"invalid content",
                "application/octet-stream",
            )
        },
    )
    
    assert unsupported_response.status_code == 415
    assert unsupported_response.json()["error"]["code"] == "HTTP_ERROR"
    assert unsupported_response.json()["error"]["message"] == (
    "Unsupported file type. Only PDF and TXT files are allowed."
)

    # PDF extension with invalid PDF signature
    invalid_pdf_response = client.post(
        "/documents/upload",
        files={
            "file": (
                "invalid.pdf",
                b"This is not a valid PDF",
                "application/pdf",
            )
        },
    )

    assert invalid_pdf_response.status_code == 415
    assert invalid_pdf_response.json()["error"]["code"] == "HTTP_ERROR"
    assert invalid_pdf_response.json()["error"]["message"] == (
        "Invalid PDF file content."
    )

    # Neither invalid upload should create a document.
    assert dependencies.documents.documents == {}
    assert dependencies.storage.files == {}
def test_indexing_failure_marks_document_as_failed(
    document_workflow_dependencies,
    client_without_server_exceptions,
    monkeypatch,
):
    dependencies = document_workflow_dependencies

    def fail_storage_read(path):
        raise OSError("Simulated storage read failure")

    monkeypatch.setattr(
        dependencies.storage,
        "read",
        fail_storage_read,
    )

    response = client_without_server_exceptions.post(
        "/documents/upload",
        files={
            "file": (
                "failure-test.txt",
                b"This document will fail during indexing.",
                "text/plain",
            )
        },
    )

    # Upload succeeds; background indexing fails afterward.
    assert response.status_code == 202

    document_id = UUID(response.json()["document_id"])

    document = dependencies.documents.get_by_id(document_id)

    assert document is not None
    assert document["status"] == DocumentStatus.FAILED

    # No partial indexing artifacts should exist.
    assert dependencies.chunks.chunks.get(document_id, []) == []
    assert dependencies.vectors.points == {}

def test_chat_without_relevant_documents_returns_fallback(
    client,
    document_workflow_dependencies,
    monkeypatch,
):
    from app.services.document import document_chat_service

    llm_called = False

    def unexpected_llm_call(prompt):
        nonlocal llm_called
        llm_called = True
        raise AssertionError("LLM should not be called for empty retrieval")

    monkeypatch.setattr(
        document_chat_service.provider,
        "invoke",
        unexpected_llm_call,
    )

    response = client.post(
        "/documents/chat",
        json={
            "question": "What is the company's travel reimbursement policy?",
            "top_k": 5,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["answer"] == (
        "I couldn't find any relevant information "
        "in the uploaded documents."
    )
    assert body["sources"] == []
    assert llm_called is False

    assert document_workflow_dependencies.chunks.chunks == {}
    assert document_workflow_dependencies.vectors.points == {}
def test_search_results_are_isolated_by_document_id(
    client,
    document_workflow_dependencies,
):
    dependencies = document_workflow_dependencies

    documents = [
        (
            "leave-policy.txt",
            (
                b"Employees receive 24 annual leave days "
                b"each year under company policy."
            ),
        ),
        (
            "travel-policy.txt",
            (
                b"Employees can claim travel reimbursement "
                b"for approved business trips."
            ),
        ),
    ]

    document_ids = []

    # Upload and index both documents through the real API.
    for filename, content in documents:
        response = client.post(
            "/documents/upload",
            files={
                "file": (filename, content, "text/plain"),
            },
        )

        assert response.status_code == 202

        document_id = UUID(response.json()["document_id"])
        document_ids.append(document_id)

        assert (
            dependencies.documents.get_by_id(document_id)["status"]
            == DocumentStatus.INDEXED
        )

    assert len(dependencies.vectors.points) > 0

    # Search specifically within the leave policy.
    leave_response = client.post(
        "/documents/search",
        json={
            "query": "annual leave days",
            "top_k": 5,
            "document_id": str(document_ids[0]),
        },
    )

    assert leave_response.status_code == 200

    leave_results = leave_response.json()["results"]

    assert leave_results
    assert all(
        result["payload"]["document_id"] == str(document_ids[0])
        for result in leave_results
    )

    # Search specifically within the travel policy.
    travel_response = client.post(
        "/documents/search",
        json={
            "query": "travel reimbursement",
            "top_k": 5,
            "document_id": str(document_ids[1]),
        },
    )

    assert travel_response.status_code == 200

    travel_results = travel_response.json()["results"]

    assert travel_results
    assert all(
        result["payload"]["document_id"] == str(document_ids[1])
        for result in travel_results
    )
def test_failed_document_is_reindexed_on_duplicate_upload(
    client_without_server_exceptions,
    document_workflow_dependencies,
    monkeypatch,
):
    dependencies = document_workflow_dependencies
    content = b"Employees receive 24 annual leave days each year."

    original_read = dependencies.storage.read
    should_fail = True

    def controlled_storage_read(path):
        if should_fail:
            raise OSError("Simulated temporary storage failure")
        return original_read(path)

    monkeypatch.setattr(
        dependencies.storage,
        "read",
        controlled_storage_read,
    )

    # First upload: indexing fails.
    first_response = client_without_server_exceptions.post(
        "/documents/upload",
        files={
            "file": (
                "leave-policy.txt",
                content,
                "text/plain",
            )
        },
    )

    assert first_response.status_code == 202

    first_body = first_response.json()
    document_id = UUID(first_body["document_id"])

    assert first_body["existing_document"] is False

    failed_document = dependencies.documents.get_by_id(document_id)

    assert failed_document["status"] == DocumentStatus.FAILED

    # Allow storage reads to succeed for the retry.
    should_fail = False

    # Second upload: identical content should trigger re-indexing.
    second_response = client_without_server_exceptions.post(
        "/documents/upload",
        files={
            "file": (
                "leave-policy.txt",
                content,
                "text/plain",
            )
        },
    )

    assert second_response.status_code == 202

    second_body = second_response.json()

    assert second_body["document_id"] == str(document_id)
    assert second_body["existing_document"] is True
    assert second_body["message"] == (
        "Existing failed document queued for re-indexing."
    )

    # Verify recovery.
    recovered_document = dependencies.documents.get_by_id(document_id)

    assert recovered_document["status"] == DocumentStatus.INDEXED

    assert len(dependencies.documents.documents) == 1
    assert dependencies.chunks.chunks[document_id]
    assert dependencies.vectors.points

    assert len(dependencies.storage.files) == 1
def test_oversized_document_upload_is_rejected(
    client,
    document_workflow_dependencies,
):
    dependencies = document_workflow_dependencies

    oversized_content = (
        b"x" * (settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
    )

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "oversized.txt",
                oversized_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "HTTP_ERROR"
    assert "maximum upload size" in (
        response.json()["error"]["message"]
    )

    assert dependencies.documents.documents == {}
    assert dependencies.storage.files == {}
def test_invalid_text_encoding_is_rejected(
    client,
    document_workflow_dependencies,
):
    dependencies = document_workflow_dependencies

    invalid_content = b"\xff\xfe\xfa\xfb"

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "invalid-encoding.txt",
                invalid_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "HTTP_ERROR"
    assert response.json()["error"]["message"] == (
        "Invalid text file encoding. UTF-8 is required."
    )

    assert dependencies.documents.documents == {}
    assert dependencies.storage.files == {}