import asyncio
from typing import List, Dict, Any, Optional
from fastembed import TextEmbedding
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

# Qdrant Credentials
QDRANT_URL = "https://ad266743-7867-4a2b-9a80-9ae7d5e914a2.us-east-1-1.aws.cloud.qdrant.io"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6NjY4ZGUzMmYtN2NlOC00Njg5LTkzOTItZmU4YzkyYTUzYTczIn0.S3MMzTZBL_oR3mZO5HWnPcz13sowlAZ-yd0Vx-YpHK8"

COLLECTION_NAME = "ghg_compliance_matrix"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
SCORE_THRESHOLD = 0.65

# -----------------------------------------------------------------------------
# Lazy Singletons for Clients & Models (Protects Async Event Loops)
# -----------------------------------------------------------------------------
class EngineSingletons:
    _qdrant_client: Optional[AsyncQdrantClient] = None
    _embedding_model: Optional[TextEmbedding] = None

    @classmethod
    def get_qdrant_client(cls) -> AsyncQdrantClient:
        if cls._qdrant_client is None:
            cls._qdrant_client = AsyncQdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY
            )
        return cls._qdrant_client

    @classmethod
    def get_embedding_model(cls) -> TextEmbedding:
        if cls._embedding_model is None:
            # Loads on CPU locally
            cls._embedding_model = TextEmbedding(EMBEDDING_MODEL_NAME)
        return cls._embedding_model

# -----------------------------------------------------------------------------
# System Prompt & Skills Template for LLM Grounding
# -----------------------------------------------------------------------------
SYSTEM_PROMPT_TEMPLATE = """
You are an elite Cloud Software Engineer and Senior ESG Systems Architect specializing in the Greenhouse Gas (GHG) Protocol framework.
You MUST act strictly based on the knowledge provided in the context below. 

IF the provided context does not contain enough information to accurately fulfill the request, you MUST reply exactly with:
"The knowledge base does not contain enough information to fulfill this request." 
Do NOT generate answers from outside the provided knowledge base (No hallucinations).

Your responses must be structured using the following mandatory 4-part format:
1. **Answer**: Direct answer to the user's inquiry.
2. **Explanation**: Detailed logic based on the GHG protocol or tool provided.
3. **Relevant GHG guidance**: Mention if this falls under Requirements, Recommendations, Best Practices, or Assumptions.
4. **Reference**: State the exact 'source_file', 'section'/'Page', and 'topic' from the metadata context.

You are equipped to execute the following operational SKILLS when applicable based on the user's query:
- **SKILL 1 (Explain Scope)**: Evaluate an activity asset (e.g. "Diesel generator"), map it to the correct GHG Scope, explain why, and cite the exact reference.
- **SKILL 2 (Find Reporting Boundary)**: Analyze a described business operation and suggest the correct organizational/operational boundaries based on the protocols.
- **SKILL 3 (Identify Missing Data)**: Review provided inputs (e.g. "electricity bill") and deduce what necessary data streams are missing (e.g. Natural gas, fleet fuel).
- **SKILL 4 (Compliance Check)**: Audit a reporting statement against mandatory requirements and highlight any missing structural categories (like Scope 3 categories).
- **SKILL 5 (Explain Recommendation)**: Provide analytical reasoning based on guidelines as to why specific components are categorized a certain way (e.g., employee commuting vs business travel).

Context blocks retrieved:
{context}

User Query:
{query}
"""

# -----------------------------------------------------------------------------
# Asynchronous Retrieval Execution
# -----------------------------------------------------------------------------
async def search_knowledge(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search the vector database for relevant text chunks based on the user query.
    Uses asyncio.to_thread for CPU-bound embedding generation.
    """
    client = EngineSingletons.get_qdrant_client()
    embedding_model = EngineSingletons.get_embedding_model()

    # Wrap the synchronous embedding generator in to_thread to avoid blocking event loop
    def embed_query(q: str):
        # TextEmbedding.embed returns a generator, we need to extract the first element
        return list(embedding_model.embed([q]))[0]

    vector = await asyncio.to_thread(embed_query, query)

    search_result = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector.tolist(),
        limit=top_k,
        score_threshold=SCORE_THRESHOLD,
        with_payload=True
    )

    results = []
    for point in search_result.points:
        results.append({
            "score": point.score,
            "text": point.payload.get("text", ""),
            "metadata": {
                "source_file": point.payload.get("source_file"),
                "document_type": point.payload.get("document_type"),
                "section": point.payload.get("section"),
                "topic": point.payload.get("topic"),
                "version_year": point.payload.get("version_year")
            }
        })
    return results

# -----------------------------------------------------------------------------
# Engine API / Helper for running the prompt formatting
# -----------------------------------------------------------------------------
async def generate_rag_prompt(query: str, top_k: int = 5) -> str:
    """Retrieves relevant context and formats the final system prompt string."""
    results = await search_knowledge(query, top_k)
    
    if not results:
        context_str = "No relevant context found in the knowledge base."
    else:
        context_blocks = []
        for idx, res in enumerate(results):
            meta = res["metadata"]
            block = (
                f"--- Context {idx+1} (Score: {res['score']:.2f}) ---\n"
                f"Source: {meta['source_file']} | Section: {meta['section']} | Topic: {meta['topic']}\n"
                f"Text:\n{res['text']}\n"
            )
            context_blocks.append(block)
        context_str = "\n".join(context_blocks)
        
    final_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context_str, query=query)
    return final_prompt

if __name__ == "__main__":
    # Simple test execution to verify everything loads and runs
    async def run_test():
        query = "Can you map a diesel generator to the correct Scope and explain why?"
        print("Running RAG Retrieval test...")
        prompt = await generate_rag_prompt(query)
        print("--- GENERATED PROMPT ---")
        print(prompt)
        
    asyncio.run(run_test())
