"""Chat Route - RAG-basierte Frage-Antwort."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.rag import RAGService

router = APIRouter()

# In-Memory Chat History (für Demo)
chat_history: list[dict] = []


class ChatRequest(BaseModel):
    question: str
    language: str = "de"  # de, en, pl
    max_sources: int = 10


class Source(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence: float
    answerable: bool  # Guardrail: "unanswerable" bei fehlender Evidenz


class HistoryItem(BaseModel):
    question: str
    answer: str
    timestamp: str
    sources_count: int
    sources: List[dict] = []  # Komplette Quellen für Wiederherstellung


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """RAG-basierte Chat-Anfrage mit Quellenangabe."""
    rag_service = RAGService()
    try:
        result = await rag_service.query(
            question=request.question,
            language=request.language,
            max_sources=request.max_sources
        )
        
        # Zur History hinzufügen
        from datetime import datetime
        chat_history.insert(0, {
            "question": request.question,
            "answer": result.get("answer", ""),
            "timestamp": datetime.now().isoformat(),
            "sources_count": len(result.get("sources", [])),
            "sources": result.get("sources", [])  # Komplette Quellen speichern
        })
        
        # History auf 50 Einträge begrenzen
        if len(chat_history) > 50:
            chat_history.pop()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[HistoryItem])
async def get_history(limit: int = 20):
    """Letzte Chat-Anfragen abrufen."""
    return chat_history[:limit]


@router.delete("/history")
async def clear_history():
    """Chat-History löschen."""
    chat_history.clear()
    return {"message": "History gelöscht"}
