# Carbon-Auditor: RAG Architecture

## 1. Purpose

This document details the architecture and integration of the Retrieval-Augmented Generation (RAG) Knowledge Engine. The system allows users to query complex GHG Protocol guidelines and receive accurate, cited answers.

> [!IMPORTANT]
> The ingestion pipeline (document parsing, chunking, and embedding generation) has already been completed. This document focuses on the *integration and retrieval* architecture implemented in the backend.

## 2. Overview of Existing RAG Infrastructure

The Knowledge Base consists of GHG Protocol PDFs and Excel calculation methodologies.
* **Embedding Model**: `BAAI/bge-small-en-v1.5` (via FastEmbed). Chosen for its high performance and low latency on CPU.
* **Vector Database**: Qdrant Cloud Serverless. Already populated with embedded vectors and metadata.
* **LLM**: Google Gemini. Used strictly for natural language synthesis based on retrieved context.

## 3. Retrieval Architecture

The RAG process is executed entirely within the backend's `rag_service.py` upon receiving a user query.

### 3.1. Workflow

1.  **User Question Formulation**: The user submits a query via the dashboard (e.g., "How do I calculate scope 2 location-based emissions?").
2.  **Query Embedding**: The backend uses FastEmbed (`BAAI/bge-small-en-v1.5`) to convert the text query into a dense vector representation.
3.  **Vector Search (Qdrant)**:
    *   The backend connects to Qdrant Cloud via its REST/gRPC API.
    *   Performs a similarity search using Cosine Similarity.
    *   Retrieves the **Top K chunks** (default K=5).
4.  **Threshold Validation**: If the highest similarity score is below a predefined threshold (e.g., 0.70), the system short-circuits and returns a generic fallback response to prevent hallucination.
5.  **Prompt Construction**: The retrieved text chunks are injected into a strict system prompt template.
6.  **LLM Synthesis (Gemini)**: Gemini generates the final answer based *only* on the provided context.

### 3.2. Prompt Engineering Template

```text
You are an expert ESG and Carbon Compliance auditor.
Use the following pieces of context retrieved from the GHG Protocol to answer the user's question.
If the answer is not contained within the context, say "I cannot find the answer in the provided GHG guidelines." DO NOT invent information.

Context:
{context_chunks}

User Question: {question}

Answer format: Provide a clear, professional answer. At the end, list the sources used.
```

## 4. Metadata Structure in Qdrant

While ingestion is complete, the retrieval system relies on the following metadata structure attached to each vector payload in Qdrant:
*   `source_file`: The name of the original PDF/Excel (e.g., "Scope2_Guidance.pdf").
*   `page_number`: The page from which the chunk was extracted.
*   `text_content`: The raw text chunk used for LLM synthesis.

## 5. API Integration Details

*   **Endpoint**: `POST /api/v1/chat/query`
*   **Latency Considerations**: FastEmbed runs locally in the Lambda function. Ensure the Lambda has at least 1024MB of RAM to load the `bge-small` model into memory quickly.

## 6. Failure Handling

| Scenario | System Response |
| :--- | :--- |
| Qdrant Cloud Timeout | Return HTTP 500 with message "Knowledge base is currently unavailable." |
| Gemini API Rate Limit | Implement exponential backoff retry (up to 3 times). If fails, return HTTP 429. |
| Off-topic User Query | The LLM prompt restricts answers to the provided context, resulting in a polite refusal to answer non-ESG queries. |

## 7. Developer Notes
*   Do not attempt to recreate the Qdrant index. Use the provided API keys in AWS Secrets Manager to connect to the existing cluster.
*   To test the retrieval logic locally without incurring Gemini costs, you can mock the Gemini API call and print the constructed prompt containing the retrieved context to the console.
