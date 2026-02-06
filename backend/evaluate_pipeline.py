"""
RAG Pipeline Evaluation System

Hochqualitative Evaluation für Masterarbeit-Präsentation.

Features:
- Dynamische Test-Queries aus verschiedenen Kategorien
- A/B Vergleich: Vector vs. Hybrid vs. Hybrid+CrossEncoder
- Metriken: Precision, Recall, MRR, Response Time, Diversity
- Ground Truth basierend auf Feedback-Kategorien

Literatur:
- RAGAS Framework (Retrieval Augmented Generation Assessment)
- BEIR Benchmark für Information Retrieval
"""

import asyncio
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import json

from services.vectorstore import VectorStoreService
from services.rag import RAGService
from services.deps import get_vectorstore


@dataclass
class EvaluationQuery:
    """Eine Testfrage mit erwarteten Kategorien."""
    query: str
    expected_categories: List[str]  # Erwartete source_types in den Ergebnissen
    difficulty: str  # easy, medium, hard
    description: str


@dataclass  
class RetrievalResult:
    """Ergebnis einer einzelnen Retrieval-Operation."""
    query: str
    retrieved_ids: List[str]
    retrieved_categories: List[str]
    expected_categories: List[str]
    precision: float
    recall: float
    mrr: float  # Mean Reciprocal Rank
    response_time_ms: float
    method: str  # vector, hybrid, hybrid+rerank
    num_results: int
    category_diversity: float  # Wie viele verschiedene Kategorien


@dataclass
class EvaluationReport:
    """Gesamtbericht einer Evaluation."""
    total_queries: int
    avg_precision: float
    avg_recall: float
    avg_mrr: float
    avg_response_time_ms: float
    avg_diversity: float
    results_by_method: Dict[str, Dict]
    results_by_difficulty: Dict[str, Dict]
    category_distribution: Dict[str, int]
    detailed_results: List[Dict]


# =============================================================================
# SPEZIALISIERTE QUERY-DATASETS
# =============================================================================
# 
# 4 Datasets für unterschiedliche Retrieval-Methoden-Stärken:
# 1. VECTOR_QUERIES: Semantische Queries (Synonyme, Paraphrasen)
# 2. HYBRID_QUERIES: Keyword-lastige Queries (technische Begriffe)
# 3. CROSSENCODER_QUERIES: Komplexe, ambigue Queries
# 4. MIXED_QUERIES: Kombination aus allen
# =============================================================================

# -----------------------------------------------------------------------------
# DATASET 1: VECTOR-OPTIMIERT
# Semantische Queries mit Synonymen und Umschreibungen
# Vector Search erkennt Bedeutung ohne exakte Keyword-Matches
# -----------------------------------------------------------------------------
VECTOR_QUERIES = [
    EvaluationQuery(
        query="Issues with finding my destination",  # Umschreibung für Navigation
        expected_categories=["navigation"],
        difficulty="easy",
        description="Paraphrase for navigation - no direct keyword"
    ),
    EvaluationQuery(
        query="The car feels too warm or too cold inside",  # Umschreibung für Climate
        expected_categories=["climate"],
        difficulty="easy",
        description="Semantic description of climate issues"
    ),
    EvaluationQuery(
        query="Entertainment and media playback concerns",  # Synonym für Infotainment
        expected_categories=["infotainment"],
        difficulty="easy",
        description="Synonym for infotainment"
    ),
    EvaluationQuery(
        query="Connecting my mobile device doesn't work",  # Umschreibung Phone
        expected_categories=["phone_connectivity"],
        difficulty="easy",
        description="Paraphrase for phone connectivity"
    ),
    EvaluationQuery(
        query="Safety features that help me drive",  # Umschreibung ADAS
        expected_categories=["driver_assistance"],
        difficulty="medium",
        description="Semantic description of driver assistance"
    ),
    EvaluationQuery(
        query="The system keeps crashing and restarting",  # Beschreibung statt Keyword
        expected_categories=["software_bug"],
        difficulty="medium",
        description="Behavior description instead of 'software bug'"
    ),
    EvaluationQuery(
        query="How reliable is this vehicle over time?",  # Frage statt Keywords
        expected_categories=["performance_reliability"],
        difficulty="medium",
        description="Question format for reliability"
    ),
    EvaluationQuery(
        query="Comfort when sitting for long periods",  # Umschreibung Interior
        expected_categories=["interior_ergonomics"],
        difficulty="medium",
        description="Semantic interior/ergonomics query"
    ),
    EvaluationQuery(
        query="How the vehicle looks and its visual appeal",  # Umschreibung Design
        expected_categories=["design_aesthetics"],
        difficulty="easy",
        description="Paraphrase for design aesthetics"
    ),
    EvaluationQuery(
        query="Money spent on fuel and maintenance",  # Umschreibung Costs
        expected_categories=["costs_environment"],
        difficulty="medium",
        description="Semantic cost description"
    ),
]

# -----------------------------------------------------------------------------
# DATASET 2: HYBRID-OPTIMIERT (BM25 + Vector)
# Queries mit spezifischen Keywords und technischen Begriffen
# BM25 findet exakte Matches, Vector versteht Kontext
# -----------------------------------------------------------------------------
HYBRID_QUERIES = [
    EvaluationQuery(
        query="GPS navigation route calculation map",  # Starke Keywords
        expected_categories=["navigation"],
        difficulty="easy",
        description="Strong navigation keywords"
    ),
    EvaluationQuery(
        query="HVAC air conditioning temperature celsius",  # Technische Begriffe
        expected_categories=["climate"],
        difficulty="medium",
        description="Technical HVAC terminology"
    ),
    EvaluationQuery(
        query="Touchscreen infotainment display MIB3",  # VW-spezifisch
        expected_categories=["infotainment"],
        difficulty="medium",
        description="VW-specific infotainment terms"
    ),
    EvaluationQuery(
        query="Bluetooth pairing CarPlay Android Auto sync",  # Produktnamen
        expected_categories=["phone_connectivity"],
        difficulty="easy",
        description="Specific product names and protocols"
    ),
    EvaluationQuery(
        query="ACC adaptive cruise control lane keeping ADAS",  # Abkürzungen
        expected_categories=["driver_assistance"],
        difficulty="medium",
        description="ADAS abbreviations and technical terms"
    ),
    EvaluationQuery(
        query="OTA update firmware version error code",  # Tech-Keywords
        expected_categories=["software_bug"],
        difficulty="medium",
        description="Software/update specific terminology"
    ),
    EvaluationQuery(
        query="Engine kW horsepower torque performance",  # Performance-Keywords
        expected_categories=["performance_reliability"],
        difficulty="easy",
        description="Engine performance metrics"
    ),
    EvaluationQuery(
        query="Seat adjustment lumbar support ergonomic",  # Ergonomie-Keywords
        expected_categories=["interior_ergonomics"],
        difficulty="easy",
        description="Ergonomics specific terms"
    ),
    EvaluationQuery(
        query="Exterior paint color metallic design",  # Design-Keywords  
        expected_categories=["design_aesthetics"],
        difficulty="easy",
        description="Design and color terminology"
    ),
    EvaluationQuery(
        query="CO2 emissions fuel economy mpg consumption",  # Umwelt-Keywords
        expected_categories=["costs_environment"],
        difficulty="medium",
        description="Environmental metrics and terms"
    ),
]

# -----------------------------------------------------------------------------
# DATASET 3: CROSSENCODER-OPTIMIERT
# Komplexe, ambigue, kontextabhängige Queries
# CrossEncoder versteht feine Nuancen und Relevanzen
# -----------------------------------------------------------------------------
CROSSENCODER_QUERIES = [
    EvaluationQuery(
        query="I can't figure out where I'm going and the directions seem confused",
        expected_categories=["navigation"],
        difficulty="hard",
        description="Long, colloquial navigation complaint"
    ),
    EvaluationQuery(
        query="Something's off with how the car regulates its internal environment",
        expected_categories=["climate"],
        difficulty="hard",
        description="Vague climate description requiring understanding"
    ),
    EvaluationQuery(
        query="The thing you touch to control music and calls keeps misbehaving",
        expected_categories=["infotainment", "phone_connectivity"],
        difficulty="hard",
        description="Ambiguous - could be infotainment or phone"
    ),
    EvaluationQuery(
        query="When I try to use my phone with the car it just won't cooperate",
        expected_categories=["phone_connectivity"],
        difficulty="medium",
        description="Colloquial phone connectivity issue"
    ),
    EvaluationQuery(
        query="The automated driving helpers seem unreliable and scary sometimes",
        expected_categories=["driver_assistance"],
        difficulty="hard",
        description="Emotional language about ADAS"
    ),
    EvaluationQuery(
        query="It randomly does things I didn't ask for and then freezes completely",
        expected_categories=["software_bug"],
        difficulty="hard",
        description="Vague software issue description"
    ),
    EvaluationQuery(
        query="I'm worried this car won't last and has hidden problems",
        expected_categories=["performance_reliability"],
        difficulty="hard",
        description="Concern-based reliability query"
    ),
    EvaluationQuery(
        query="Sitting in here for hours makes my back hurt and controls are awkward",
        expected_categories=["interior_ergonomics"],
        difficulty="medium",
        description="Experience-based ergonomics feedback"
    ),
    EvaluationQuery(
        query="I wish this car looked more exciting and less boring from outside",
        expected_categories=["design_aesthetics"],
        difficulty="medium",
        description="Opinion-based design feedback"
    ),
    EvaluationQuery(
        query="Between what I pay and what I get, I'm not sure it's worth it environmentally",
        expected_categories=["costs_environment"],
        difficulty="hard",
        description="Complex value/environment trade-off"
    ),
    # Cross-category complex queries
    EvaluationQuery(
        query="Everything digital in this car seems to have issues - screens, connections, updates",
        expected_categories=["infotainment", "phone_connectivity", "software_bug"],
        difficulty="hard",
        description="Multi-category technology issues"
    ),
    EvaluationQuery(
        query="I love how it looks but hate how it drives and feels inside",
        expected_categories=["design_aesthetics", "performance_reliability", "interior_ergonomics"],
        difficulty="hard",
        description="Contradictory multi-aspect feedback"
    ),
]

# -----------------------------------------------------------------------------
# DATASET 4: MIXED (Alle kombiniert)
# Repräsentative Mischung aus allen drei Typen
# Zeigt Gesamtperformance über verschiedene Query-Typen
# -----------------------------------------------------------------------------
MIXED_QUERIES = (
    VECTOR_QUERIES[:4] +      # 4 semantische
    HYBRID_QUERIES[:4] +      # 4 keyword-basierte
    CROSSENCODER_QUERIES[:4]  # 4 komplexe
)

# Legacy: Original TEST_QUERIES für Backwards-Kompatibilität
TEST_QUERIES = MIXED_QUERIES

# Dataset-Lookup für API
QUERY_DATASETS = {
    "vector": VECTOR_QUERIES,
    "hybrid": HYBRID_QUERIES,
    "crossencoder": CROSSENCODER_QUERIES,
    "mixed": MIXED_QUERIES,
}


class PipelineEvaluator:
    """
    Evaluiert die RAG-Pipeline mit verschiedenen Konfigurationen.
    
    Vergleicht:
    1. Nur Vector Search
    2. Hybrid Search (BM25 + Vector)
    3. Hybrid + Cross-Encoder Reranking
    """
    
    def __init__(self):
        self.vectorstore = VectorStoreService()
    
    async def evaluate_single_query(
        self,
        query: EvaluationQuery,
        use_hybrid: bool = True,
        use_reranking: bool = True,
        top_k: int = 10
    ) -> RetrievalResult:
        """Einzelne Query evaluieren."""
        
        # Retrieval ausführen
        start_time = time.time()
        results = await self.vectorstore.search(
            query=query.query,
            top_k=top_k,
            use_hybrid=use_hybrid,
            use_reranking=use_reranking
        )
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Ergebnisse analysieren
        retrieved_ids = [r["id"] for r in results]
        # Nutze 'label' statt 'source_type' und konvertiere zu lowercase
        retrieved_categories = [r["metadata"].get("label", r["metadata"].get("source_type", "unknown")).lower() for r in results]
        
        # Precision: Anteil relevanter Ergebnisse
        relevant_count = sum(1 for cat in retrieved_categories if cat in query.expected_categories)
        precision = relevant_count / len(results) if results else 0
        
        # Recall: Wie viele erwartete Kategorien wurden gefunden?
        found_categories = set(retrieved_categories) & set(query.expected_categories)
        recall = len(found_categories) / len(query.expected_categories) if query.expected_categories else 0
        
        # MRR: Rang des ersten relevanten Ergebnisses
        mrr = 0
        for i, cat in enumerate(retrieved_categories):
            if cat in query.expected_categories:
                mrr = 1 / (i + 1)
                break
        
        # Diversity: Wie viele verschiedene Kategorien
        unique_categories = len(set(retrieved_categories))
        diversity = unique_categories / len(results) if results else 0
        
        # Method bestimmen
        if use_reranking:
            method = "hybrid+rerank"
        elif use_hybrid:
            method = "hybrid"
        else:
            method = "vector"
        
        return RetrievalResult(
            query=query.query,
            retrieved_ids=retrieved_ids,
            retrieved_categories=retrieved_categories,
            expected_categories=query.expected_categories,
            precision=precision,
            recall=recall,
            mrr=mrr,
            response_time_ms=elapsed_ms,
            method=method,
            num_results=len(results),
            category_diversity=diversity
        )
    
    async def run_full_evaluation(
        self,
        queries: List[EvaluationQuery] = None,
        compare_methods: bool = True
    ) -> Dict:
        """
        Vollständige Evaluation durchführen.
        
        Args:
            queries: Testfragen (default: alle vordefinierten)
            compare_methods: A/B Vergleich der Methoden
        """
        if queries is None:
            queries = TEST_QUERIES
        
        all_results = []
        
        if compare_methods:
            # Alle drei Methoden vergleichen
            methods = [
                {"use_hybrid": False, "use_reranking": False, "name": "vector"},
                {"use_hybrid": True, "use_reranking": False, "name": "hybrid"},
                {"use_hybrid": True, "use_reranking": True, "name": "hybrid+rerank"},
            ]
        else:
            # Nur beste Methode
            methods = [
                {"use_hybrid": True, "use_reranking": True, "name": "hybrid+rerank"},
            ]
        
        for query in queries:
            for method in methods:
                result = await self.evaluate_single_query(
                    query=query,
                    use_hybrid=method["use_hybrid"],
                    use_reranking=method["use_reranking"]
                )
                all_results.append({
                    **asdict(result),
                    "difficulty": query.difficulty,
                    "description": query.description
                })
        
        # Aggregieren
        report = self._aggregate_results(all_results, queries)
        return report
    
    def _aggregate_results(self, results: List[Dict], queries: List[EvaluationQuery]) -> Dict:
        """Ergebnisse aggregieren und Report erstellen."""
        
        # Nach Methode gruppieren
        by_method = defaultdict(list)
        for r in results:
            by_method[r["method"]].append(r)
        
        # Nach Schwierigkeit gruppieren
        by_difficulty = defaultdict(list)
        for r in results:
            by_difficulty[r["difficulty"]].append(r)
        
        # Kategorie-Verteilung
        category_counts = defaultdict(int)
        for r in results:
            for cat in r["retrieved_categories"]:
                category_counts[cat] += 1
        
        # Durchschnitte pro Methode
        method_stats = {}
        for method, method_results in by_method.items():
            method_stats[method] = {
                "avg_precision": sum(r["precision"] for r in method_results) / len(method_results),
                "avg_recall": sum(r["recall"] for r in method_results) / len(method_results),
                "avg_mrr": sum(r["mrr"] for r in method_results) / len(method_results),
                "avg_response_time_ms": sum(r["response_time_ms"] for r in method_results) / len(method_results),
                "avg_diversity": sum(r["category_diversity"] for r in method_results) / len(method_results),
                "num_queries": len(method_results)
            }
        
        # Durchschnitte pro Schwierigkeit
        difficulty_stats = {}
        for diff, diff_results in by_difficulty.items():
            difficulty_stats[diff] = {
                "avg_precision": sum(r["precision"] for r in diff_results) / len(diff_results),
                "avg_recall": sum(r["recall"] for r in diff_results) / len(diff_results),
                "avg_mrr": sum(r["mrr"] for r in diff_results) / len(diff_results),
                "num_queries": len(diff_results)
            }
        
        # Gesamtdurchschnitte (nur beste Methode für Hauptmetriken)
        best_method_results = by_method.get("hybrid+rerank", results)
        
        return {
            "total_queries": len(queries),
            "total_evaluations": len(results),
            "avg_precision": sum(r["precision"] for r in best_method_results) / len(best_method_results),
            "avg_recall": sum(r["recall"] for r in best_method_results) / len(best_method_results),
            "avg_mrr": sum(r["mrr"] for r in best_method_results) / len(best_method_results),
            "avg_response_time_ms": sum(r["response_time_ms"] for r in best_method_results) / len(best_method_results),
            "avg_diversity": sum(r["category_diversity"] for r in best_method_results) / len(best_method_results),
            "results_by_method": method_stats,
            "results_by_difficulty": difficulty_stats,
            "category_distribution": dict(category_counts),
            "detailed_results": results,
            "improvement_summary": self._calculate_improvements(method_stats)
        }
    
    def _calculate_improvements(self, method_stats: Dict) -> Dict:
        """Verbesserungen zwischen Methoden berechnen."""
        if "vector" not in method_stats or "hybrid+rerank" not in method_stats:
            return {}
        
        vector = method_stats["vector"]
        hybrid = method_stats.get("hybrid", vector)
        rerank = method_stats["hybrid+rerank"]
        
        return {
            "hybrid_vs_vector": {
                "precision_improvement": f"+{((hybrid['avg_precision'] / max(vector['avg_precision'], 0.001)) - 1) * 100:.1f}%",
                "recall_improvement": f"+{((hybrid['avg_recall'] / max(vector['avg_recall'], 0.001)) - 1) * 100:.1f}%",
                "mrr_improvement": f"+{((hybrid['avg_mrr'] / max(vector['avg_mrr'], 0.001)) - 1) * 100:.1f}%"
            },
            "rerank_vs_hybrid": {
                "precision_improvement": f"+{((rerank['avg_precision'] / max(hybrid['avg_precision'], 0.001)) - 1) * 100:.1f}%",
                "recall_improvement": f"+{((rerank['avg_recall'] / max(hybrid['avg_recall'], 0.001)) - 1) * 100:.1f}%",
                "mrr_improvement": f"+{((rerank['avg_mrr'] / max(hybrid['avg_mrr'], 0.001)) - 1) * 100:.1f}%"
            },
            "rerank_vs_vector": {
                "precision_improvement": f"+{((rerank['avg_precision'] / max(vector['avg_precision'], 0.001)) - 1) * 100:.1f}%",
                "recall_improvement": f"+{((rerank['avg_recall'] / max(vector['avg_recall'], 0.001)) - 1) * 100:.1f}%",
                "mrr_improvement": f"+{((rerank['avg_mrr'] / max(vector['avg_mrr'], 0.001)) - 1) * 100:.1f}%"
            }
        }


async def run_evaluation():
    """Evaluation im Terminal ausführen."""
    print("=" * 60)
    print("🔬 RAG Pipeline Evaluation")
    print("=" * 60)
    
    evaluator = PipelineEvaluator()
    
    print(f"\n📊 Starte Evaluation mit {len(TEST_QUERIES)} Testfragen...")
    print("   Vergleiche: Vector vs. Hybrid vs. Hybrid+CrossEncoder")
    print()
    
    report = await evaluator.run_full_evaluation(compare_methods=True)
    
    # Ergebnisse anzeigen
    print("\n" + "=" * 60)
    print("📈 ERGEBNISSE")
    print("=" * 60)
    
    print("\n🎯 Gesamt (beste Methode: Hybrid+Rerank):")
    print(f"   Precision:     {report['avg_precision']:.2%}")
    print(f"   Recall:        {report['avg_recall']:.2%}")
    print(f"   MRR:           {report['avg_mrr']:.2%}")
    print(f"   Response Time: {report['avg_response_time_ms']:.0f}ms")
    print(f"   Diversity:     {report['avg_diversity']:.2%}")
    
    print("\n📊 Vergleich der Methoden:")
    print("-" * 60)
    print(f"{'Methode':<20} {'Precision':<12} {'Recall':<12} {'MRR':<12} {'Zeit':<10}")
    print("-" * 60)
    for method, stats in report["results_by_method"].items():
        print(f"{method:<20} {stats['avg_precision']:<12.2%} {stats['avg_recall']:<12.2%} {stats['avg_mrr']:<12.2%} {stats['avg_response_time_ms']:<10.0f}ms")
    
    if report.get("improvement_summary"):
        print("\n🚀 Verbesserungen:")
        imp = report["improvement_summary"]
        print(f"   Hybrid vs Vector:        Precision {imp['hybrid_vs_vector']['precision_improvement']}, MRR {imp['hybrid_vs_vector']['mrr_improvement']}")
        print(f"   Rerank vs Hybrid:        Precision {imp['rerank_vs_hybrid']['precision_improvement']}, MRR {imp['rerank_vs_hybrid']['mrr_improvement']}")
        print(f"   Rerank vs Vector (TOTAL): Precision {imp['rerank_vs_vector']['precision_improvement']}, MRR {imp['rerank_vs_vector']['mrr_improvement']}")
    
    print("\n📁 Ergebnisse nach Schwierigkeit:")
    for diff, stats in report["results_by_difficulty"].items():
        print(f"   {diff}: Precision {stats['avg_precision']:.2%}, Recall {stats['avg_recall']:.2%}")
    
    # JSON speichern
    with open("evaluation_report.json", "w", encoding="utf-8") as f:
        # Detailed results kürzen für JSON
        report_copy = {k: v for k, v in report.items() if k != "detailed_results"}
        report_copy["detailed_results_count"] = len(report["detailed_results"])
        json.dump(report_copy, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Report gespeichert: evaluation_report.json")
    print("=" * 60)
    
    return report


if __name__ == "__main__":
    asyncio.run(run_evaluation())
