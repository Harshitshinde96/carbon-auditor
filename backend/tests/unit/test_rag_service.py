import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.rag_service import RAGService
from app.core.exceptions import RAGQdrantTimeoutError, RAGGeminiRateLimitError


@pytest.fixture
def mock_qdrant():
    with patch("app.services.rag_service.AsyncQdrantClient") as mock_client:
        instance = mock_client.return_value
        yield instance


@pytest.fixture
def mock_fastembed():
    with patch("app.services.rag_service.TextEmbedding") as mock_embed:
        instance = mock_embed.return_value
        yield instance


@pytest.fixture
def mock_gemini():
    with patch("app.services.rag_service.genai") as mock_genai:
        yield mock_genai


@pytest.mark.asyncio
async def test_top_score_above_threshold(mock_qdrant, mock_fastembed, mock_gemini):
    # Setup Qdrant to return a score >= 0.70
    mock_point = MagicMock()
    mock_point.score = 0.854
    mock_point.payload = {
        "text": "Scope 1 emissions include direct emissions.",
        "source_file": "GHG_Protocol.pdf",
        "section": "Chapter 3",
        "topic": "Scope 1",
    }

    mock_qdrant.query_points = AsyncMock()
    mock_qdrant.query_points.return_value.points = [mock_point]

    # Mock embedding
    import numpy as np

    mock_fastembed.embed.return_value = [np.array([0.1, 0.2, 0.3])]

    # Mock Gemini
    mock_model = mock_gemini.GenerativeModel.return_value
    mock_model.generate_content_async = AsyncMock(
        return_value=MagicMock(text="Yes, Scope 1 includes direct emissions.")
    )

    service = RAGService()
    result = await service.query("What is scope 1?")

    assert result["confidence_score"] == 0.85
    assert result["sources"] == [
        {"source_file": "GHG_Protocol.pdf", "section": "Chapter 3"}
    ]
    assert result["answer"] == "Yes, Scope 1 includes direct emissions."
    mock_model.generate_content_async.assert_called_once()


@pytest.mark.asyncio
async def test_top_score_below_threshold(mock_qdrant, mock_fastembed, mock_gemini):
    # Setup Qdrant to return a score < 0.70
    mock_point = MagicMock()
    mock_point.score = 0.651
    mock_point.payload = {
        "text": "Some irrelevant text",
        "source_file": "random.pdf",
        "section": "1",
    }

    mock_qdrant.query_points = AsyncMock()
    mock_qdrant.query_points.return_value.points = [mock_point]

    import numpy as np

    mock_fastembed.embed.return_value = [np.array([0.1, 0.2, 0.3])]

    mock_model = mock_gemini.GenerativeModel.return_value
    mock_model.generate_content_async = AsyncMock()

    service = RAGService()
    result = await service.query("How to bake a cake?")

    assert result["confidence_score"] == 0.65
    assert result["sources"] == []
    assert (
        result["answer"]
        == "The knowledge base does not contain enough information to fulfill this request."
    )

    # Assert Gemini is NEVER called when below threshold
    mock_model.generate_content_async.assert_not_called()


@pytest.mark.asyncio
async def test_qdrant_timeout(mock_qdrant, mock_fastembed, mock_gemini):
    import numpy as np

    mock_fastembed.embed.return_value = [np.array([0.1, 0.2, 0.3])]

    import httpx

    # Simulate a timeout from the async qdrant client
    mock_qdrant.query_points = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

    service = RAGService()
    with pytest.raises(RAGQdrantTimeoutError) as exc:
        await service.query("Test timeout")

    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_gemini_rate_limit(mock_qdrant, mock_fastembed, mock_gemini):
    mock_point = MagicMock()
    mock_point.score = 0.90
    mock_point.payload = {
        "text": "Valid text",
        "source_file": "doc.pdf",
        "section": "1",
    }

    mock_qdrant.query_points = AsyncMock()
    mock_qdrant.query_points.return_value.points = [mock_point]
    import numpy as np

    mock_fastembed.embed.return_value = [np.array([0.1, 0.2, 0.3])]

    from google.api_core.exceptions import ResourceExhausted

    mock_model = mock_gemini.GenerativeModel.return_value
    mock_model.generate_content_async = AsyncMock(
        side_effect=ResourceExhausted("Rate limit exceeded")
    )

    service = RAGService()

    # We should retry 3 times (initial + 2 retries) or (initial + 3 retries)? The PRD says "(<=3 retries) then 429".
    # I'll assert it raises our 429 mapped error.

    # Mock asyncio.sleep so the test runs instantly instead of actually waiting for exponential backoff
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(RAGGeminiRateLimitError) as exc:
            await service.query("Test rate limit")

        assert exc.value.status_code == 429
        # Should have slept for backoff
        assert mock_sleep.call_count >= 2
        assert mock_model.generate_content_async.call_count > 1
