from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from app.services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService()


class ChatRequest(BaseModel):
    query: str


@router.post("/query")
async def chat_query(request: ChatRequest) -> Dict[str, Any]:
    result = await rag_service.query(request.query)
    return {"status": "success", "data": result}
