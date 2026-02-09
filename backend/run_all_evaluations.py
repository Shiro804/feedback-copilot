"""
Comprehensive RAG Pipeline Evaluation

Führt Evaluation für alle 4 Datasets durch:
- VECTOR_QUERIES (semantische Queries)
- HYBRID_QUERIES (keyword-basierte Queries)  
- CROSSENCODER_QUERIES (komplexe Queries)
- MIXED_QUERIES (kombiniert)

Berechnet Durchschnitte für jede Methode über alle Datasets.
"""

import asyncio
import json
from evaluate_pipeline import (
    PipelineEvaluator,
    VECTOR_QUERIES,
    HYBRID_QUERIES,
    CROSSENCODER_QUERIES,
    MIXED_QUERIES
)

DATASETS = {
    "vector": VECTOR_QUERIES,
    "hybrid": HYBRID_QUERIES,
    "crossencoder": CROSSENCODER_QUERIES,
    "mixed": MIXED_QUERIES
}

async def run_all_evaluations():
    """Alle Datasets evaluieren und Durchschnitte berechnen."""
    print("=" * 70)
    print("🔬 COMPREHENSIVE RAG PIPELINE EVALUATION")
    print("=" * 70)
    
    evaluator = PipelineEvaluator()
    all_results = {}
    
    # Für jedes Dataset evaluieren
    for dataset_name, queries in DATASETS.items():
        print(f"\n📊 Evaluiere Dataset: {dataset_name.upper()} ({len(queries)} Queries)")
        print("-" * 50)
        
        report = await evaluator.run_full_evaluation(queries=queries, compare_methods=True)
        all_results[dataset_name] = report
        
        # Kurze Zusammenfassung
        for method, stats in report["results_by_method"].items():
            print(f"   {method:20} P={stats['avg_precision']:.1%} R={stats['avg_recall']:.1%} MRR={stats['avg_mrr']:.1%} {stats['avg_response_time_ms']:.0f}ms")
    
    # Durchschnitte über alle Datasets berechnen
    print("\n" + "=" * 70)
    print("📈 DURCHSCHNITTE ÜBER ALLE DATASETS")
    print("=" * 70)
    
    methods = ["vector", "hybrid", "hybrid+rerank"]
    aggregated = {method: {"precision": [], "recall": [], "mrr": [], "time": []} for method in methods}
    
    # Sammle Werte pro Methode über alle Datasets
    for dataset_name, report in all_results.items():
        for method in methods:
            if method in report["results_by_method"]:
                stats = report["results_by_method"][method]
                aggregated[method]["precision"].append(stats["avg_precision"])
                aggregated[method]["recall"].append(stats["avg_recall"])
                aggregated[method]["mrr"].append(stats["avg_mrr"])
                aggregated[method]["time"].append(stats["avg_response_time_ms"])
    
    # Berechne finale Durchschnitte
    final_averages = {}
    print(f"\n{'Methode':<20} {'Precision':<12} {'Recall':<12} {'MRR':<12} {'Latenz (ms)':<12}")
    print("-" * 70)
    
    for method in methods:
        avg_precision = sum(aggregated[method]["precision"]) / len(aggregated[method]["precision"])
        avg_recall = sum(aggregated[method]["recall"]) / len(aggregated[method]["recall"])
        avg_mrr = sum(aggregated[method]["mrr"]) / len(aggregated[method]["mrr"])
        avg_time = sum(aggregated[method]["time"]) / len(aggregated[method]["time"])
        
        final_averages[method] = {
            "avg_precision": avg_precision,
            "avg_recall": avg_recall,
            "avg_mrr": avg_mrr,
            "avg_response_time_ms": avg_time
        }
        
        print(f"{method:<20} {avg_precision:<12.1%} {avg_recall:<12.1%} {avg_mrr:<12.1%} {avg_time:<12.0f}")
    
    # Pro Dataset-Ergebnisse
    print("\n" + "=" * 70)
    print("📁 ERGEBNISSE PRO DATASET UND METHODE")
    print("=" * 70)
    
    for dataset_name, report in all_results.items():
        print(f"\n### {dataset_name.upper()} ({report['total_queries']} Queries)")
        print(f"{'Methode':<20} {'Precision':<12} {'Recall':<12} {'MRR':<12} {'Latenz':<10}")
        for method, stats in report["results_by_method"].items():
            print(f"{method:<20} {stats['avg_precision']:<12.1%} {stats['avg_recall']:<12.1%} {stats['avg_mrr']:<12.1%} {stats['avg_response_time_ms']:<10.0f}ms")
    
    # Speichern als JSON
    output = {
        "timestamp": "2026-02-09T08:44:00Z",
        "datasets_evaluated": list(DATASETS.keys()),
        "total_queries_per_dataset": {name: len(queries) for name, queries in DATASETS.items()},
        "final_averages_across_all_datasets": final_averages,
        "per_dataset_results": {
            name: {
                method: stats for method, stats in report["results_by_method"].items()
            } for name, report in all_results.items()
        }
    }
    
    with open("comprehensive_evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Vollständiger Report gespeichert: comprehensive_evaluation_report.json")
    print("=" * 70)
    
    return output

if __name__ == "__main__":
    asyncio.run(run_all_evaluations())
