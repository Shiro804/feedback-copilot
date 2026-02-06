"""
Search Route - Hybrid Retrieval (BM25 + Vector)

Literatur:
- Praneeth et al. (2025): RAG Fusion + hierarchisches Chunk-Retrieval
- Nguyen et al. (2024): Intent-Filtered RAG
- Gao et al. (2024): ScaNN für effizientes Retrieval
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from services.vectorstore import VectorStoreService

router = APIRouter()
vectorstore = VectorStoreService()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    use_hybrid: bool = True  # BM25 + Vector
    filters: Optional[dict] = None


class SearchResult(BaseModel):
    id: str
    text: str
    score: float
    source_type: str
    metadata: dict


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    search_type: str  # hybrid, vector, bm25


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Hybrid Search: BM25 + Vector (aus Onepager).
    
    Literatur-basiert:
    - BM25 für Keyword-Matching
    - Vector für semantische Ähnlichkeit
    - Optional: Reranker für bessere Precision
    """
    results = await vectorstore.search(
        query=request.query,
        top_k=request.top_k,
        use_hybrid=request.use_hybrid,
        filters=request.filters
    )
    
    return SearchResponse(
        results=results,
        total=len(results),
        search_type="hybrid" if request.use_hybrid else "vector"
    )


@router.get("/similar/{doc_id}")
async def find_similar(doc_id: str, top_k: int = 5):
    """Ähnliche Dokumente zu einem gegebenen Dokument finden."""
    results = await vectorstore.find_similar(doc_id, top_k)
    return {"similar": results}
