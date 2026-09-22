import asyncio
import httpx
from typing import List, Dict, Any
from fastembed import TextEmbedding
from qdrant_client import AsyncQdrantClient

from app.core.config import settings
from app.core.exceptions import RAGQdrantTimeoutError
from app.core.rag_prompts import SYSTEM_PROMPT_TEMPLATE
from app.core.llm_client import OpenRouterClient


class RAGService:
    def __init__(self):
        self.qdrant_client = AsyncQdrantClient(
            url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=10.0
        )
        self.collection_name = "ghg_compliance_matrix"
        # Loaded once globally per instance (or use a singleton approach for the embedding model if preferred,
        # but here we initialize it once for the service).
        self.embedding_model = TextEmbedding("BAAI/bge-small-en-v1.5")

        # Configure LLM Client
        self.llm = OpenRouterClient()

    async def _embed_query(self, query: str) -> List[float]:
        # TextEmbedding.embed returns a generator, so we extract the first element
        def _embed():
            return list(self.embedding_model.embed([query]))[0].tolist()

        return await asyncio.to_thread(_embed)

    async def _search_qdrant(self, vector: List[float], top_k: int = 5) -> List[Any]:
        try:
            search_result = await self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=vector,
                limit=top_k,
                with_payload=True,
            )
            return search_result.points
        except httpx.TimeoutException as e:
            raise RAGQdrantTimeoutError(f"Qdrant timeout: {str(e)}")
        except Exception as e:
            if "Not found: Collection" in str(e):
                return []
            raise

    async def _generate_gemini_response(self, prompt: str) -> str:
        # Renamed variable internally but keeping method name same to avoid refactoring usages
        return await self.llm.generate_content(prompt)

    async def query(self, user_query: str) -> Dict[str, Any]:
        """
        Retrieves context and generates an answer using RAG.
        """
        vector = await self._embed_query(user_query)
        points = await self._search_qdrant(vector, top_k=5)

        if not points:
            return {
                "answer": "The knowledge base does not contain enough information to fulfill this request.",
                "sources": [],
                "confidence_score": 0.0,
            }

        # Get the highest score
        top_score = max(p.score for p in points)
        confidence_score = round(top_score, 2)

        if top_score < 0.70:
            return {
                "answer": "The knowledge base does not contain enough information to fulfill this request.",
                "sources": [],
                "confidence_score": confidence_score,
            }

        # Build context
        context_blocks = []
        sources = []

        for idx, point in enumerate(points):
            meta = point.payload

            # Extract relevant source metadata for the response
            source_file = meta.get("source_file", "Unknown")
            section = meta.get("section", "Unknown")

            # De-duplicate sources in the final output
            source_entry = {"source_file": source_file, "section": section}
            if source_entry not in sources:
                sources.append(source_entry)

            block = (
                f"--- Context {idx+1} (Score: {point.score:.2f}) ---\n"
                f"Source: {source_file} | Section: {section} | Topic: {meta.get('topic', 'Unknown')}\n"
                f"Text:\n{meta.get('text', '')}\n"
            )
            context_blocks.append(block)

        context_str = "\n".join(context_blocks)
        prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context_str, query=user_query)

        answer = await self._generate_gemini_response(prompt)

        return {
            "answer": answer,
            "sources": sources,
            "confidence_score": confidence_score,
        }
