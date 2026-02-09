"use client";

import React, { useState, useEffect } from "react";

// =============================================================================
// TYPES
// =============================================================================

interface Dataset {
    id: string;
    name: string;
    description: string;
    count: number;
    best_method: string;
}

interface MethodResult {
    method: string;
    avg_precision: number;
    avg_recall: number;
    avg_mrr: number;
    avg_response_time_ms: number;
    avg_diversity: number;
    num_queries: number;
}

interface SingleQueryResult {
    method: string;
    precision: number;
    recall: number;
    mrr: number;
    response_time_ms: number;
    retrieved_categories: string[];
    retrieved_ids: string[];
}

interface TestQuery {
    query: string;
    expected_categories: string[];
    difficulty: string;
    description: string;
}

interface PipelineData {
    vector: { precision: number; recall: number; mrr: number; response_time_ms?: number };
    hybrid: { precision: number; recall: number; mrr: number; response_time_ms?: number };
    rerank: { precision: number; recall: number; mrr: number; response_time_ms?: number };
}

// =============================================================================
// SHARED COMPONENT: Pipeline Evolution Visualization
// =============================================================================

function PipelineEvolution({ data, title, subtitle }: { data: PipelineData; title?: string; subtitle?: string }) {
    const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

    const calcWeightedScore = (metrics: { precision: number; recall: number; mrr: number }) => {
        return (metrics.mrr * 0.5) + (metrics.precision * 0.3) + (metrics.recall * 0.2);
    };

    // Metric descriptions for tooltips
    const metricInfo: Record<string, { icon: string; label: string; description: string; weight: number }> = {
        precision: {
            icon: "🎯",
            label: "Precision",
            description: "Anteil der relevanten Dokumente unter allen abgerufenen. Hohe Precision = wenig irrelevante Ergebnisse im Context.",
            weight: 30
        },
        recall: {
            icon: "📊",
            label: "Recall",
            description: "Anteil der gefundenen relevanten Dokumente. Hoher Recall = nichts Wichtiges übersehen.",
            weight: 20
        },
        mrr: {
            icon: "🏆",
            label: "MRR",
            description: "Mean Reciprocal Rank - Position des ersten relevanten Ergebnisses. Entscheidend für RAG: Top-Dokument = beste LLM-Antwort!",
            weight: 50
        },
        response_time_ms: {
            icon: "⚡",
            label: "Latenz",
            description: "Durchschnittliche Antwortzeit in Millisekunden. Niedrigere Werte = schnellere Suche.",
            weight: 0
        }
    };

    // Custom Tooltip Component
    const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

    const Tooltip = ({ id, children, content, weight }: { id: string; children: React.ReactNode; content: string; weight: number }) => (
        <div
            style={{ position: "relative", display: "inline-flex" }}
            onMouseEnter={() => setActiveTooltip(id)}
            onMouseLeave={() => setActiveTooltip(null)}
        >
            {children}
            {activeTooltip === id && (
                <div style={{
                    position: "absolute",
                    bottom: "calc(100% + 8px)",
                    left: "50%",
                    transform: "translateX(-50%)",
                    background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
                    border: "1px solid rgba(96, 165, 250, 0.3)",
                    borderRadius: "10px",
                    padding: "0.75rem 1rem",
                    width: "220px",
                    boxShadow: "0 10px 40px rgba(0,0,0,0.4)",
                    zIndex: 1000,
                    animation: "fadeIn 0.15s ease-out"
                }}>
                    {/* Arrow */}
                    <div style={{
                        position: "absolute",
                        bottom: "-6px",
                        left: "50%",
                        transform: "translateX(-50%) rotate(45deg)",
                        width: "12px",
                        height: "12px",
                        background: "#0f172a",
                        borderRight: "1px solid rgba(96, 165, 250, 0.3)",
                        borderBottom: "1px solid rgba(96, 165, 250, 0.3)"
                    }} />
                    {/* Weight Badge */}
                    <div style={{
                        display: "inline-block",
                        background: "rgba(59, 130, 246, 0.2)",
                        color: "#60a5fa",
                        fontSize: "0.65rem",
                        fontWeight: "bold",
                        padding: "2px 6px",
                        borderRadius: "4px",
                        marginBottom: "0.5rem"
                    }}>
                        Gewicht: {weight}%
                    </div>
                    {/* Description */}
                    <div style={{ color: "#e2e8f0", fontSize: "0.8rem", lineHeight: "1.4" }}>
                        {content}
                    </div>
                </div>
            )}
        </div>
    );

    const renderMetricRow = (metricKey: string, value: number) => {
        const info = metricInfo[metricKey];
        const isTimeMetric = metricKey === "response_time_ms";
        const displayValue = isTimeMetric ? `${value.toFixed(0)}ms` : formatPercent(value);
        return (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Tooltip id={`${metricKey}-${value}`} content={info.description} weight={info.weight}>
                    <span style={{ color: "rgba(255,255,255,0.8)", fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "0.25rem", cursor: "help" }}>
                        {info.icon} {info.label}
                        <span style={{
                            fontSize: "0.55rem",
                            background: "rgba(255,255,255,0.15)",
                            borderRadius: "50%",
                            width: "14px",
                            height: "14px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            marginLeft: "2px"
                        }}>?</span>
                    </span>
                </Tooltip>
                <span style={{ color: "#fff", fontWeight: "bold", fontSize: "1rem" }}>{displayValue}</span>
            </div>
        );
    };

    const renderChangeBadge = (diff: number) => (
        <div style={{
            fontSize: "0.75rem",
            fontWeight: "bold",
            color: diff >= 0 ? "#4ade80" : "#f87171",
            background: diff >= 0 ? "rgba(74,222,128,0.2)" : "rgba(248,113,113,0.2)",
            padding: "4px 8px",
            borderRadius: "4px",
            textAlign: "center",
            minWidth: "60px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: "1.5rem"
        }}>
            →{diff >= 0 ? "+" : ""}{diff.toFixed(1)}%
        </div>
    );

    const changes1 = {
        precision: (data.hybrid.precision - data.vector.precision) * 100,
        recall: (data.hybrid.recall - data.vector.recall) * 100,
        mrr: (data.hybrid.mrr - data.vector.mrr) * 100
    };

    const changes2 = {
        precision: (data.rerank.precision - data.hybrid.precision) * 100,
        recall: (data.rerank.recall - data.hybrid.recall) * 100,
        mrr: (data.rerank.mrr - data.hybrid.mrr) * 100
    };

    const totalChanges = {
        precision: (data.rerank.precision - data.vector.precision) * 100,
        recall: (data.rerank.recall - data.vector.recall) * 100,
        mrr: (data.rerank.mrr - data.vector.mrr) * 100
    };

    const scores = [
        { key: "vector", name: "🔵 Vector", score: calcWeightedScore(data.vector) },
        { key: "hybrid", name: "🟡 Hybrid", score: calcWeightedScore(data.hybrid) },
        { key: "rerank", name: "🟢 Rerank", score: calcWeightedScore(data.rerank) }
    ].sort((a, b) => b.score - a.score);

    const winner = scores[0];

    return (
        <div style={{ background: "rgba(255, 255, 255, 0.05)", borderRadius: "16px", padding: "1.5rem", marginBottom: "2rem", border: "1px solid rgba(255, 255, 255, 0.1)" }}>
            <h2 style={{ color: "#fff", marginBottom: "0.5rem", fontSize: "1.25rem" }}>{title || "🔄 Retrieval-Pipeline Evolution"}</h2>
            <p style={{ color: "#94a3b8", fontSize: "0.875rem", marginBottom: "1.5rem" }}>{subtitle || "Schrittweise Verbesserung der Pipeline mit allen Metriken"}</p>

            {/* Pipeline Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr auto 1fr", gap: "0.5rem", marginBottom: "2rem", alignItems: "stretch" }}>

                {/* Step 1: Vector */}
                <div style={{
                    background: "linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)",
                    borderRadius: "12px",
                    padding: "1.25rem",
                    position: "relative",
                    display: "flex",
                    flexDirection: "column"
                }}>
                    <div style={{ position: "absolute", top: "0.5rem", left: "0.75rem", background: "rgba(255,255,255,0.2)", borderRadius: "50%", width: "28px", height: "28px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.875rem", fontWeight: "bold", color: "#fff" }}>1</div>
                    <div style={{ marginTop: "1.25rem" }}>
                        <div style={{ color: "#fff", fontWeight: "bold", fontSize: "1.1rem" }}>🔵 Vector Search</div>
                        <div style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.8rem", marginBottom: "1rem" }}>Reine semantische Ähnlichkeit</div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                            {renderMetricRow("precision", data.vector.precision)}
                            {renderMetricRow("recall", data.vector.recall)}
                            {renderMetricRow("mrr", data.vector.mrr)}
                            {data.vector.response_time_ms !== undefined && renderMetricRow("response_time_ms", data.vector.response_time_ms)}
                        </div>
                    </div>
                </div>

                {/* Arrow 1 */}
                <div style={{ display: "flex", flexDirection: "column", justifyContent: "flex-end", alignItems: "center", padding: "0 0.5rem", paddingBottom: "1.25rem" }}>
                    <div style={{ height: "2.8rem" }}></div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                        {renderChangeBadge(changes1.precision)}
                        {renderChangeBadge(changes1.recall)}
                        {renderChangeBadge(changes1.mrr)}
                    </div>
                </div>

                {/* Step 2: Hybrid */}
                <div style={{
                    background: "linear-gradient(135deg, #a16207 0%, #eab308 100%)",
                    borderRadius: "12px",
                    padding: "1.25rem",
                    position: "relative",
                    display: "flex",
                    flexDirection: "column"
                }}>
                    <div style={{ position: "absolute", top: "0.5rem", left: "0.75rem", background: "rgba(255,255,255,0.2)", borderRadius: "50%", width: "28px", height: "28px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.875rem", fontWeight: "bold", color: "#fff" }}>2</div>
                    <div style={{ marginTop: "1.25rem" }}>
                        <div style={{ color: "#fff", fontWeight: "bold", fontSize: "1.1rem" }}>🟡 + BM25 Hybrid</div>
                        <div style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.8rem", marginBottom: "1rem" }}>+ Keyword-Matching</div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                            {renderMetricRow("precision", data.hybrid.precision)}
                            {renderMetricRow("recall", data.hybrid.recall)}
                            {renderMetricRow("mrr", data.hybrid.mrr)}
                            {data.hybrid.response_time_ms !== undefined && renderMetricRow("response_time_ms", data.hybrid.response_time_ms)}
                        </div>
                    </div>
                </div>

                {/* Arrow 2 */}
                <div style={{ display: "flex", flexDirection: "column", justifyContent: "flex-end", alignItems: "center", padding: "0 0.5rem", paddingBottom: "1.25rem" }}>
                    <div style={{ height: "2.8rem" }}></div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                        {renderChangeBadge(changes2.precision)}
                        {renderChangeBadge(changes2.recall)}
                        {renderChangeBadge(changes2.mrr)}
                    </div>
                </div>

                {/* Step 3: Rerank */}
                <div style={{
                    background: "linear-gradient(135deg, #166534 0%, #22c55e 100%)",
                    borderRadius: "12px",
                    padding: "1.25rem",
                    position: "relative",
                    display: "flex",
                    flexDirection: "column"
                }}>
                    <div style={{ position: "absolute", top: "0.5rem", left: "0.75rem", background: "rgba(255,255,255,0.2)", borderRadius: "50%", width: "28px", height: "28px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.875rem", fontWeight: "bold", color: "#fff" }}>3</div>
                    <div style={{ marginTop: "1.25rem" }}>
                        <div style={{ color: "#fff", fontWeight: "bold", fontSize: "1.1rem" }}>🟢 + CrossEncoder</div>
                        <div style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.8rem", marginBottom: "1rem" }}>+ Reranking</div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                            {renderMetricRow("precision", data.rerank.precision)}
                            {renderMetricRow("recall", data.rerank.recall)}
                            {renderMetricRow("mrr", data.rerank.mrr)}
                            {data.rerank.response_time_ms !== undefined && renderMetricRow("response_time_ms", data.rerank.response_time_ms)}
                        </div>
                    </div>
                </div>
            </div>

            {/* Total Change Summary */}
            <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: "1rem",
                marginBottom: "1.5rem",
                padding: "1rem",
                background: "rgba(255,255,255,0.03)",
                borderRadius: "12px"
            }}>
                {[
                    { label: "🎯 Precision", diff: totalChanges.precision, from: data.vector.precision, to: data.rerank.precision },
                    { label: "📊 Recall", diff: totalChanges.recall, from: data.vector.recall, to: data.rerank.recall },
                    { label: "🏆 MRR", diff: totalChanges.mrr, from: data.vector.mrr, to: data.rerank.mrr }
                ].map(({ label, diff, from, to }) => (
                    <div key={label} style={{ textAlign: "center" }}>
                        <div style={{ color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.5rem" }}>{label} Gesamt</div>
                        <div style={{
                            fontSize: "1.25rem",
                            fontWeight: "bold",
                            color: diff >= 0 ? "#4ade80" : "#f87171",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "0.25rem"
                        }}>
                            <span>{diff >= 0 ? "↑" : "↓"}</span>
                            <span>{diff >= 0 ? "+" : ""}{diff.toFixed(1)}%</span>
                        </div>
                        <div style={{ color: "#64748b", fontSize: "0.7rem" }}>
                            {formatPercent(from)} → {formatPercent(to)}
                        </div>
                    </div>
                ))}
            </div>

            {/* Weighted Winner */}
            <div style={{ background: "rgba(59, 130, 246, 0.1)", borderRadius: "8px", padding: "1rem", border: "1px solid rgba(59, 130, 246, 0.2)" }}>
                <div style={{ color: "#60a5fa", fontWeight: "500", marginBottom: "0.75rem" }}>💡 Gewichtetes Ranking (MRR 50%, Precision 30%, Recall 20%)</div>
                <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem", flexWrap: "wrap" }}>
                    {scores.map((m, idx) => (
                        <div key={m.key} style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 0.75rem", borderRadius: "8px", background: idx === 0 ? "rgba(34,197,94,0.2)" : "rgba(255,255,255,0.05)", border: idx === 0 ? "1px solid rgba(34,197,94,0.4)" : "1px solid rgba(255,255,255,0.1)" }}>
                            <span style={{ fontSize: "0.875rem", fontWeight: idx === 0 ? "bold" : "normal", color: idx === 0 ? "#4ade80" : "#94a3b8" }}>#{idx + 1}</span>
                            <span style={{ color: "#fff", fontWeight: "500" }}>{m.name}</span>
                            <span style={{ fontSize: "0.75rem", color: idx === 0 ? "#4ade80" : "#64748b" }}>({(m.score * 100).toFixed(1)}%)</span>
                        </div>
                    ))}
                </div>
                <div style={{ color: "#94a3b8", fontSize: "0.875rem", borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: "0.75rem" }}>
                    <strong style={{ color: "#fff" }}>{winner.name}</strong> gewinnt mit <strong style={{ color: "#4ade80" }}>{(winner.score * 100).toFixed(1)}%</strong> Gesamtscore.
                    {winner.key === "vector" && " Semantische Queries performen am besten mit reiner Vector-Suche."}
                    {winner.key === "hybrid" && " BM25-Keywords verbessern die Ergebnisse bei diesem Dataset."}
                    {winner.key === "rerank" && " Der CrossEncoder liefert das beste Ranking durch tieferes Verständnis."}
                    <br /><span style={{ fontSize: "0.8rem", color: "#64748b" }}>💡 MRR (50%) ist entscheidend für RAG - je höher das Top-Ergebnis, desto besser die LLM-Antwort.</span>
                </div>
            </div>
        </div>
    );
}

// =============================================================================
// MAIN PAGE COMPONENT
// =============================================================================

export default function EvaluationPage() {
    // Mode: "single" or "dataset"
    const [mode, setMode] = useState<"single" | "dataset">("dataset");

    // Dataset mode state
    const [isRunning, setIsRunning] = useState(false);
    const [datasetResults, setDatasetResults] = useState<PipelineData | null>(null);
    const [numQueries, setNumQueries] = useState(10);
    const [selectedDataset, setSelectedDataset] = useState("mixed");
    const [datasets, setDatasets] = useState<Dataset[]>([]);

    // Single query mode state
    const [isTesting, setIsTesting] = useState(false);
    const [singleResults, setSingleResults] = useState<PipelineData | null>(null);
    const [testQueries, setTestQueries] = useState<TestQuery[]>([]);
    const [categories, setCategories] = useState<string[]>([]);
    const [customQuery, setCustomQuery] = useState("");
    const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

    useEffect(() => {
        fetch("http://localhost:8000/api/evaluate/datasets")
            .then(res => res.json())
            .then(data => setDatasets(data))
            .catch(console.error);
        fetch("http://localhost:8000/api/evaluate/categories")
            .then(res => res.json())
            .then(data => setCategories(data))
            .catch(console.error);
    }, []);

    useEffect(() => {
        fetch(`http://localhost:8000/api/evaluate/test-queries?dataset=${selectedDataset}`)
            .then(res => res.json())
            .then(data => setTestQueries(data))
            .catch(console.error);
    }, [selectedDataset]);

    const runDatasetEvaluation = async () => {
        setIsRunning(true);
        setDatasetResults(null);
        try {
            const res = await fetch("http://localhost:8000/api/evaluate/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    num_queries: numQueries,
                    compare_methods: true,
                    random_order: true,
                    dataset: selectedDataset
                })
            });
            if (res.ok) {
                const data = await res.json();
                // Convert to PipelineData format
                setDatasetResults({
                    vector: {
                        precision: data.results_by_method["vector"]?.avg_precision || 0,
                        recall: data.results_by_method["vector"]?.avg_recall || 0,
                        mrr: data.results_by_method["vector"]?.avg_mrr || 0,
                        response_time_ms: data.results_by_method["vector"]?.avg_response_time_ms
                    },
                    hybrid: {
                        precision: data.results_by_method["hybrid"]?.avg_precision || 0,
                        recall: data.results_by_method["hybrid"]?.avg_recall || 0,
                        mrr: data.results_by_method["hybrid"]?.avg_mrr || 0,
                        response_time_ms: data.results_by_method["hybrid"]?.avg_response_time_ms
                    },
                    rerank: {
                        precision: data.results_by_method["hybrid+rerank"]?.avg_precision || 0,
                        recall: data.results_by_method["hybrid+rerank"]?.avg_recall || 0,
                        mrr: data.results_by_method["hybrid+rerank"]?.avg_mrr || 0,
                        response_time_ms: data.results_by_method["hybrid+rerank"]?.avg_response_time_ms
                    }
                });
            }
        } catch (error) {
            console.error("Evaluation failed:", error);
        } finally {
            setIsRunning(false);
        }
    };

    const runSingleQuery = async () => {
        if (!customQuery.trim()) return;
        setIsTesting(true);
        setSingleResults(null);
        try {
            const res = await fetch("http://localhost:8000/api/evaluate/single", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: customQuery,
                    expected_categories: selectedCategories
                })
            });
            if (res.ok) {
                const data = await res.json();
                // Convert single query results to PipelineData format
                const results = data.results as SingleQueryResult[];
                const vectorResult = results.find(r => r.method === "vector");
                const hybridResult = results.find(r => r.method === "hybrid");
                const rerankResult = results.find(r => r.method === "hybrid+rerank");

                setSingleResults({
                    vector: {
                        precision: vectorResult?.precision || 0,
                        recall: vectorResult?.recall || 0,
                        mrr: vectorResult?.mrr || 0,
                        response_time_ms: vectorResult?.response_time_ms
                    },
                    hybrid: {
                        precision: hybridResult?.precision || 0,
                        recall: hybridResult?.recall || 0,
                        mrr: hybridResult?.mrr || 0,
                        response_time_ms: hybridResult?.response_time_ms
                    },
                    rerank: {
                        precision: rerankResult?.precision || 0,
                        recall: rerankResult?.recall || 0,
                        mrr: rerankResult?.mrr || 0,
                        response_time_ms: rerankResult?.response_time_ms
                    }
                });
            }
        } catch (error) {
            console.error("Query test failed:", error);
        } finally {
            setIsTesting(false);
        }
    };

    const selectPredefinedQuery = (query: TestQuery) => {
        setCustomQuery(query.query);
        setSelectedCategories(query.expected_categories);
    };

    const toggleCategory = (cat: string) => {
        setSelectedCategories(prev =>
            prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]
        );
    };

    const currentDataset = datasets.find(d => d.id === selectedDataset);
    const currentResults = mode === "dataset" ? datasetResults : singleResults;
    const isLoading = mode === "dataset" ? isRunning : isTesting;

    return (
        <>
            {/* CSS Animation for Tooltips */}
            <style>{`
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateX(-50%) translateY(5px); }
                    to { opacity: 1; transform: translateX(-50%) translateY(0); }
                }
            `}</style>
            <div style={{ minHeight: "100vh", background: "linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%)", padding: "2rem" }}>
                <div style={{ maxWidth: "1400px", margin: "0 auto" }}>

                    {/* Header */}
                    <div style={{ textAlign: "center", marginBottom: "2rem" }}>
                        <h1 style={{ fontSize: "2.5rem", fontWeight: "bold", color: "#fff", marginBottom: "0.5rem" }}>
                            🔬 RAG Pipeline Evaluation
                        </h1>
                        <p style={{ color: "#94a3b8", fontSize: "1.1rem" }}>
                            Vergleiche Vector Search, Hybrid (BM25) und CrossEncoder Reranking
                        </p>
                    </div>

                    {/* Mode Toggle */}
                    <div style={{ display: "flex", justifyContent: "center", marginBottom: "2rem" }}>
                        <div style={{
                            background: "rgba(255, 255, 255, 0.05)",
                            borderRadius: "12px",
                            padding: "0.25rem",
                            display: "inline-flex",
                            border: "1px solid rgba(255, 255, 255, 0.1)"
                        }}>
                            <button
                                onClick={() => setMode("dataset")}
                                style={{
                                    padding: "0.75rem 2rem",
                                    borderRadius: "10px",
                                    border: "none",
                                    cursor: "pointer",
                                    fontWeight: "600",
                                    fontSize: "1rem",
                                    transition: "all 0.2s",
                                    background: mode === "dataset" ? "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)" : "transparent",
                                    color: mode === "dataset" ? "#fff" : "#94a3b8"
                                }}
                            >
                                📊 Dataset Evaluation
                            </button>
                            <button
                                onClick={() => setMode("single")}
                                style={{
                                    padding: "0.75rem 2rem",
                                    borderRadius: "10px",
                                    border: "none",
                                    cursor: "pointer",
                                    fontWeight: "600",
                                    fontSize: "1rem",
                                    transition: "all 0.2s",
                                    background: mode === "single" ? "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)" : "transparent",
                                    color: mode === "single" ? "#fff" : "#94a3b8"
                                }}
                            >
                                🔍 Einzelne Query
                            </button>
                        </div>
                    </div>

                    {/* Dataset Mode */}
                    {mode === "dataset" && (
                        <>
                            {/* Dataset Selection */}
                            <div style={{ background: "rgba(255, 255, 255, 0.05)", borderRadius: "16px", padding: "1.5rem", marginBottom: "2rem", border: "1px solid rgba(255, 255, 255, 0.1)" }}>
                                <h2 style={{ color: "#fff", marginBottom: "1rem", fontSize: "1.1rem" }}>📁 Dataset auswählen</h2>
                                <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginBottom: "1.5rem" }}>
                                    {datasets.map(dataset => (
                                        <button
                                            key={dataset.id}
                                            onClick={() => setSelectedDataset(dataset.id)}
                                            style={{
                                                padding: "0.75rem 1.25rem",
                                                borderRadius: "10px",
                                                border: selectedDataset === dataset.id ? "2px solid #60a5fa" : "1px solid rgba(255,255,255,0.2)",
                                                background: selectedDataset === dataset.id ? "rgba(59, 130, 246, 0.2)" : "rgba(255,255,255,0.05)",
                                                color: "#fff",
                                                cursor: "pointer",
                                                textAlign: "left"
                                            }}
                                        >
                                            <div style={{ fontWeight: "bold" }}>{dataset.name}</div>
                                            <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>{dataset.count} Queries</div>
                                        </button>
                                    ))}
                                </div>

                                {/* Controls */}
                                <div style={{ display: "flex", gap: "1rem", alignItems: "flex-end", flexWrap: "wrap" }}>
                                    <div>
                                        <label style={{ color: "#94a3b8", fontSize: "0.875rem", display: "block", marginBottom: "0.5rem" }}>Anzahl Testfragen</label>
                                        <select value={numQueries} onChange={(e) => setNumQueries(parseInt(e.target.value))} style={{ background: "#1e3a5f", color: "#fff", border: "1px solid rgba(255, 255, 255, 0.2)", borderRadius: "8px", padding: "0.625rem 1rem", fontSize: "1rem", height: "44px" }}>
                                            <option value={5}>5 Fragen</option>
                                            <option value={10}>10 Fragen</option>
                                            <option value={12}>Alle ({currentDataset?.count || 12})</option>
                                        </select>
                                    </div>
                                    <button onClick={runDatasetEvaluation} disabled={isRunning} style={{ background: isRunning ? "#475569" : "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)", color: "#fff", border: "none", borderRadius: "8px", padding: "0 2rem", fontSize: "1rem", fontWeight: "600", cursor: isRunning ? "not-allowed" : "pointer", display: "flex", alignItems: "center", gap: "0.5rem", height: "44px" }}>
                                        {isRunning ? <>⏳ Läuft...</> : <>🚀 Evaluation starten</>}
                                    </button>
                                </div>
                            </div>
                        </>
                    )}

                    {/* Single Query Mode */}
                    {mode === "single" && (
                        <>
                            {/* Query Input */}
                            <div style={{ background: "rgba(255, 255, 255, 0.05)", borderRadius: "16px", padding: "1.5rem", marginBottom: "2rem", border: "1px solid rgba(255, 255, 255, 0.1)" }}>
                                <h2 style={{ color: "#fff", marginBottom: "1rem", fontSize: "1.1rem" }}>🔍 Query eingeben</h2>

                                {/* Predefined Queries */}
                                <div style={{ marginBottom: "1.5rem" }}>
                                    <label style={{ color: "#94a3b8", fontSize: "0.875rem", display: "block", marginBottom: "0.5rem" }}>Vordefinierte Queries</label>
                                    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                                        {testQueries.slice(0, 5).map((q, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => selectPredefinedQuery(q)}
                                                style={{
                                                    padding: "0.5rem 1rem",
                                                    borderRadius: "8px",
                                                    border: "1px solid rgba(255,255,255,0.2)",
                                                    background: customQuery === q.query ? "rgba(59, 130, 246, 0.2)" : "rgba(255,255,255,0.05)",
                                                    color: "#fff",
                                                    cursor: "pointer",
                                                    fontSize: "0.875rem",
                                                    maxWidth: "200px",
                                                    overflow: "hidden",
                                                    textOverflow: "ellipsis",
                                                    whiteSpace: "nowrap"
                                                }}
                                                title={q.query}
                                            >
                                                {q.query}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Custom Query Input */}
                                <div style={{ marginBottom: "1.5rem" }}>
                                    <label style={{ color: "#94a3b8", fontSize: "0.875rem", display: "block", marginBottom: "0.5rem" }}>Eigene Query</label>
                                    <input
                                        type="text"
                                        value={customQuery}
                                        onChange={(e) => setCustomQuery(e.target.value)}
                                        placeholder="z.B. Wie verbessere ich meine Bewerbung?"
                                        style={{
                                            width: "100%",
                                            padding: "0.75rem 1rem",
                                            borderRadius: "8px",
                                            border: "1px solid rgba(255,255,255,0.2)",
                                            background: "#1e3a5f",
                                            color: "#fff",
                                            fontSize: "1rem"
                                        }}
                                    />
                                </div>

                                {/* Category Selection */}
                                <div style={{ marginBottom: "1.5rem" }}>
                                    <label style={{ color: "#94a3b8", fontSize: "0.875rem", display: "block", marginBottom: "0.5rem" }}>Erwartete Kategorien (für Precision/Recall)</label>
                                    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                                        {categories.map(cat => (
                                            <button
                                                key={cat}
                                                onClick={() => toggleCategory(cat)}
                                                style={{
                                                    padding: "0.4rem 0.8rem",
                                                    borderRadius: "6px",
                                                    border: selectedCategories.includes(cat) ? "2px solid #60a5fa" : "1px solid rgba(255,255,255,0.2)",
                                                    background: selectedCategories.includes(cat) ? "rgba(59, 130, 246, 0.2)" : "rgba(255,255,255,0.05)",
                                                    color: selectedCategories.includes(cat) ? "#60a5fa" : "#94a3b8",
                                                    cursor: "pointer",
                                                    fontSize: "0.8rem"
                                                }}
                                            >
                                                {cat}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Run Button */}
                                <button onClick={runSingleQuery} disabled={isTesting || !customQuery.trim()} style={{ background: isTesting || !customQuery.trim() ? "#475569" : "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)", color: "#fff", border: "none", borderRadius: "8px", padding: "0.75rem 2rem", fontSize: "1rem", fontWeight: "600", cursor: isTesting || !customQuery.trim() ? "not-allowed" : "pointer", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                    {isTesting ? <>⏳ Teste...</> : <>🔍 Query testen</>}
                                </button>
                            </div>
                        </>
                    )}

                    {/* Loading State */}
                    {isLoading && (
                        <div style={{ textAlign: "center", padding: "3rem", color: "#94a3b8" }}>
                            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>⏳</div>
                            <div>Evaluiere Pipeline-Methoden...</div>
                        </div>
                    )}

                    {/* Results - Same component for both modes! */}
                    {currentResults && !isLoading && (
                        <PipelineEvolution
                            data={currentResults}
                            title={mode === "single" ? `🔍 Ergebnis für: "${customQuery}"` : undefined}
                            subtitle={mode === "single" ? `Kategorien: ${selectedCategories.join(", ") || "Keine ausgewählt"}` : undefined}
                        />
                    )}
                </div>
            </div>
        </>
    );
}
