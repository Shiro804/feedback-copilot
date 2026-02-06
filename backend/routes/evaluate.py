"""
Evaluation API Routes

Endpoints für die visuelle Evaluation-Page.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Literal
import asyncio

from evaluate_pipeline import (
    PipelineEvaluator, 
    TEST_QUERIES, 
    QUERY_DATASETS,
    VECTOR_QUERIES,
    HYBRID_QUERIES,
    CROSSENCODER_QUERIES,
    MIXED_QUERIES,
    EvaluationQuery
)

router = APIRouter()


class EvaluationRequest(BaseModel):
    """Request für Evaluation."""
    num_queries: int = 10  # Anzahl der Testfragen
    compare_methods: bool = True  # Alle Methoden vergleichen
    random_order: bool = True  # Zufällige Reihenfolge
    dataset: Literal["vector", "hybrid", "crossencoder", "mixed"] = "mixed"


class SingleQueryRequest(BaseModel):
    """Request für einzelne Query-Evaluation."""
    query: str
    expected_categories: List[str] = []
    use_hybrid: bool = True
    use_reranking: bool = True


@router.post("/run")
async def run_evaluation(request: EvaluationRequest):
    """
    Vollständige Evaluation durchführen.
    
    Returns:
        Evaluation Report mit allen Metriken
    """
    evaluator = PipelineEvaluator()
    
    # Dataset auswählen
    queries = QUERY_DATASETS.get(request.dataset, MIXED_QUERIES).copy()
    
    if request.random_order:
        import random
        random.shuffle(queries)
    
    queries = queries[:request.num_queries]
    
    report = await evaluator.run_full_evaluation(
        queries=queries,
        compare_methods=request.compare_methods
    )
    
    # Dataset-Info hinzufügen
    report["dataset_used"] = request.dataset
    report["dataset_description"] = {
        "vector": "Semantische Queries (Synonyme, Paraphrasen) - optimiert für Vector Search",
        "hybrid": "Keyword-lastige Queries (technische Begriffe) - optimiert für BM25+Vector",
        "crossencoder": "Komplexe, ambigue Queries - optimiert für CrossEncoder Reranking",
        "mixed": "Gemischte Auswahl aus allen drei Query-Typen"
    }.get(request.dataset, "")
    
    return report


@router.post("/single")
async def evaluate_single_query(request: SingleQueryRequest):
    """
    Einzelne Query evaluieren mit allen drei Methoden.
    """
    evaluator = PipelineEvaluator()
    
    query = EvaluationQuery(
        query=request.query,
        expected_categories=request.expected_categories if request.expected_categories else [],
        difficulty="custom",
        description="User-defined query"
    )
    
    # Alle drei Methoden testen
    results = []
    
    # 1. Vector only
    result_vector = await evaluator.evaluate_single_query(
        query=query,
        use_hybrid=False,
        use_reranking=False
    )
    results.append({
        "method": "vector",
        "precision": result_vector.precision,
        "recall": result_vector.recall,
        "mrr": result_vector.mrr,
        "response_time_ms": result_vector.response_time_ms,
        "retrieved_categories": result_vector.retrieved_categories,
        "retrieved_ids": result_vector.retrieved_ids
    })
    
    # 2. Hybrid
    result_hybrid = await evaluator.evaluate_single_query(
        query=query,
        use_hybrid=True,
        use_reranking=False
    )
    results.append({
        "method": "hybrid",
        "precision": result_hybrid.precision,
        "recall": result_hybrid.recall,
        "mrr": result_hybrid.mrr,
        "response_time_ms": result_hybrid.response_time_ms,
        "retrieved_categories": result_hybrid.retrieved_categories,
        "retrieved_ids": result_hybrid.retrieved_ids
    })
    
    # 3. Hybrid + Rerank
    result_rerank = await evaluator.evaluate_single_query(
        query=query,
        use_hybrid=True,
        use_reranking=True
    )
    results.append({
        "method": "hybrid+rerank",
        "precision": result_rerank.precision,
        "recall": result_rerank.recall,
        "mrr": result_rerank.mrr,
        "response_time_ms": result_rerank.response_time_ms,
        "retrieved_categories": result_rerank.retrieved_categories,
        "retrieved_ids": result_rerank.retrieved_ids
    })
    
    return {
        "query": request.query,
        "expected_categories": request.expected_categories,
        "results": results
    }


@router.get("/test-queries")
async def get_test_queries(dataset: str = "mixed"):
    """Vordefinierte Testfragen abrufen."""
    queries = QUERY_DATASETS.get(dataset, MIXED_QUERIES)
    return [
        {
            "query": q.query,
            "expected_categories": q.expected_categories,
            "difficulty": q.difficulty,
            "description": q.description
        }
        for q in queries
    ]


@router.get("/datasets")
async def get_datasets():
    """Verfügbare Datasets mit Beschreibungen abrufen."""
    return [
        {
            "id": "vector",
            "name": "🔵 Vector-Optimiert",
            "description": "Semantische Queries mit Synonymen und Paraphrasen",
            "count": len(VECTOR_QUERIES),
            "best_method": "vector"
        },
        {
            "id": "hybrid",
            "name": "🟡 Hybrid-Optimiert",
            "description": "Keyword-lastige Queries mit technischen Begriffen",
            "count": len(HYBRID_QUERIES),
            "best_method": "hybrid"
        },
        {
            "id": "crossencoder",
            "name": "🟢 CrossEncoder-Optimiert",
            "description": "Komplexe, ambigue Queries",
            "count": len(CROSSENCODER_QUERIES),
            "best_method": "hybrid+rerank"
        },
        {
            "id": "mixed",
            "name": "⚪ Gemischt",
            "description": "Kombination aus allen Query-Typen",
            "count": len(MIXED_QUERIES),
            "best_method": "hybrid+rerank"
        }
    ]


@router.get("/categories")
async def get_categories():
    """Verfügbare Kategorien abrufen."""
    return [
        "navigation",
        "climate", 
        "infotainment",
        "phone_connectivity",
        "driver_assistance",
        "software_bug",
        "performance_reliability",
        "interior_ergonomics",
        "design_aesthetics",
        "costs_environment"
    ]
