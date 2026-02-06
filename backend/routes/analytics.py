"""
Analytics Route - Trend-Analyse und Aggregationen

Aus Onepager:
- Trend/Top-Aspekte als Charts
- Zeitbasierte Analyse

Update: Jetzt mit echten Daten aus VectorStore
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from collections import Counter

from services.vectorstore import VectorStoreService

router = APIRouter()
vectorstore = VectorStoreService()


class TrendPoint(BaseModel):
    date: str
    count: int
    sentiment_avg: Optional[float] = None


class AspectCount(BaseModel):
    aspect: str
    count: int
    sentiment: str  # positive, neutral, negative


class AnalyticsResponse(BaseModel):
    total_feedbacks: int
    date_range: dict
    trends: List[TrendPoint]
    top_aspects: List[AspectCount]
    sentiment_distribution: dict


@router.get("/overview", response_model=AnalyticsResponse)
async def get_overview(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    model: Optional[str] = None,
    market: Optional[str] = None
):
    """
    Übersicht über Feedback-Trends und Top-Aspekte.
    Nutzt echte Daten aus dem VectorStore.
    
    Filter:
    - Zeitraum
    - Fahrzeugmodell
    - Markt
    """
    # Echte Daten aus VectorStore laden
    results = vectorstore.collection.get(include=["metadatas"], limit=10000)
    
    if not results or not results.get("metadatas"):
        # Fallback für leeren VectorStore
        return AnalyticsResponse(
            total_feedbacks=0,
            date_range={"start": "", "end": ""},
            trends=[],
            top_aspects=[],
            sentiment_distribution={"positive": 0, "neutral": 0, "negative": 0}
        )
    
    metadatas = results["metadatas"]
    
    # Filter anwenden
    if model:
        metadatas = [m for m in metadatas if m.get("vehicle_model") == model]
    if market:
        metadatas = [m for m in metadatas if m.get("market") == market]
    
    total = len(metadatas)
    
    # Labels (=Kategorien) zählen für Top-Aspekte
    label_counts = Counter()
    style_counts = Counter()
    dates = []
    
    for meta in metadatas:
        label = meta.get("label")
        style = meta.get("style")
        timestamp = meta.get("timestamp")
        
        if label:
            label_counts[label] += 1
        if style:
            style_counts[style] += 1
        if timestamp:
            # Nur Datum extrahieren
            try:
                date_str = timestamp[:10]
                dates.append(date_str)
            except:
                pass
    
    # Top-Aspekte erstellen
    top_aspects = []
    for label, count in label_counts.most_common(10):
        # Sentiment basierend auf Style approximieren
        sentiment = "neutral"
        if "complaint" in str(style_counts.get(label, "")):
            sentiment = "negative"
        elif "praise" in str(style_counts.get(label, "")):
            sentiment = "positive"
        
        top_aspects.append(AspectCount(
            aspect=label,
            count=count,
            sentiment=sentiment
        ))
    
    # Sentiment Distribution aus Style-Verteilung
    total_styles = sum(style_counts.values())
    if total_styles > 0:
        sentiment_dist = {
            "positive": round(style_counts.get("praise", 0) / total_styles, 2),
            "neutral": round((style_counts.get("neutral_observation", 0) + 
                            style_counts.get("question", 0)) / total_styles, 2),
            "negative": round(style_counts.get("complaint", 0) / total_styles, 2)
        }
    else:
        sentiment_dist = {"positive": 0.33, "neutral": 0.34, "negative": 0.33}
    
    # Datum-Trends berechnen
    date_counts = Counter(dates)
    trends = []
    for date, count in sorted(date_counts.items())[-30:]:  # Letzte 30 Tage
        trends.append(TrendPoint(date=date, count=count))
    
    # Datum-Range
    if dates:
        date_range = {"start": min(dates), "end": max(dates)}
    else:
        date_range = {"start": "", "end": ""}
    
    return AnalyticsResponse(
        total_feedbacks=total,
        date_range=date_range,
        trends=trends,
        top_aspects=top_aspects,
        sentiment_distribution=sentiment_dist
    )


@router.get("/aspects")
async def get_aspects(top_k: int = 20):
    """Top-Aspekte aus dem Feedback."""
    results = vectorstore.collection.get(include=["metadatas"], limit=10000)
    
    if not results or not results.get("metadatas"):
        return {"aspects": [], "total": 0}
    
    label_counts = Counter()
    for meta in results["metadatas"]:
        label = meta.get("label")
        if label:
            label_counts[label] += 1
    
    aspects = [{"aspect": label, "count": count} 
               for label, count in label_counts.most_common(top_k)]
    
    return {"aspects": aspects, "total": len(label_counts)}


@router.get("/sentiment")
async def get_sentiment_trends():
    """Sentiment-Verlauf über Zeit basierend auf Style."""
    results = vectorstore.collection.get(include=["metadatas"], limit=10000)
    
    if not results or not results.get("metadatas"):
        return {"trends": []}
    
    style_counts = Counter()
    for meta in results["metadatas"]:
        style = meta.get("style")
        if style:
            style_counts[style] += 1
    
    return {
        "by_style": dict(style_counts),
        "total": sum(style_counts.values())
    }


@router.get("/models")
async def get_model_stats():
    """Feedback-Statistiken nach Fahrzeugmodell."""
    results = vectorstore.collection.get(include=["metadatas"], limit=10000)
    
    if not results or not results.get("metadatas"):
        return {"models": [], "total": 0}
    
    model_counts = Counter()
    for meta in results["metadatas"]:
        model = meta.get("vehicle_model")
        if model:
            model_counts[model] += 1
    
    models = [{"model": m, "count": c} 
              for m, c in model_counts.most_common()]
    
    return {"models": models, "total": len(model_counts)}


@router.get("/markets")
async def get_market_stats():
    """Feedback-Statistiken nach Markt."""
    results = vectorstore.collection.get(include=["metadatas"], limit=10000)
    
    if not results or not results.get("metadatas"):
        return {"markets": [], "total": 0}
    
    market_counts = Counter()
    for meta in results["metadatas"]:
        market = meta.get("market")
        if market:
            market_counts[market] += 1
    
    markets = [{"market": m, "count": c} 
               for m, c in market_counts.most_common()]
    
    return {"markets": markets, "total": len(market_counts)}


@router.get("/sources")
async def get_source_stats():
    """Feedback-Statistiken nach Quelle (voice, touch, error)."""
    results = vectorstore.collection.get(include=["metadatas"], limit=10000)
    
    if not results or not results.get("metadatas"):
        return {"sources": [], "total": 0}
    
    source_counts = Counter()
    for meta in results["metadatas"]:
        source = meta.get("source_type")
        if source:
            source_counts[source] += 1
    
    sources = [{"source": s, "count": c} 
               for s, c in source_counts.most_common()]
    
    return {"sources": sources, "total": len(source_counts)}
