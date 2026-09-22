import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Patch AsyncQdrantClient before importing app to avoid event loop issues
with patch("app.services.rag_service.AsyncQdrantClient"):
    from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_rag():
    with patch("app.api.v1.chat.rag_service.query", new_callable=AsyncMock) as mock:
        yield mock


def test_chat_query_success(mock_rag):
    mock_rag.return_value = {
        "answer": "This is a synthesized answer.",
        "sources": [{"source_file": "doc.pdf", "section": "1"}],
        "confidence_score": 0.95,
    }

    response = client.post("/api/v1/chat/query", json={"query": "What is scope 1?"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["answer"] == "This is a synthesized answer."
    assert len(data["sources"]) == 1
    assert data["confidence_score"] == 0.95


def test_chat_query_low_confidence(mock_rag):
    mock_rag.return_value = {
        "answer": "The knowledge base does not contain enough information to fulfill this request.",
        "sources": [],
        "confidence_score": 0.55,
    }

    response = client.post("/api/v1/chat/query", json={"query": "Unknown topic?"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert (
        data["answer"]
        == "The knowledge base does not contain enough information to fulfill this request."
    )
    assert len(data["sources"]) == 0
    assert data["confidence_score"] == 0.55
