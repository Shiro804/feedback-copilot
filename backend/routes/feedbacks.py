"""
Feedback Route - Übersicht und Einzelansicht

Angepasst für den neuen 10K Datensatz mit Feldern:
- label (Kategorie wie NAVIGATION, etc.)
- style (praise, complaint, question, neutral_observation)
- length_bucket (short, medium)
- meta (Generierungs-Infos)
- self_check (predicted_label, is_feedback, confidence)

Endpoints:
- GET /feedbacks - Alle Feedbacks mit Metadaten
- GET /feedbacks/{id} - Einzelansicht
- GET /feedbacks/stats - Statistiken für Dashboard
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from services.deps import get_vectorstore

router = APIRouter()


class FeedbackItem(BaseModel):
    id: str
    text: str
    label: str  # Kategorie (NAVIGATION, etc.)
    style: str  # praise, complaint, question, neutral_observation
    length_bucket: str  # short, medium
    confidence: float  # aus self_check
    # Legacy-Felder für Kompatibilität
    source_type: Optional[str] = None
    language: Optional[str] = None
    timestamp: Optional[str] = None
    vehicle_model: Optional[str] = None
    market: Optional[str] = None


class FeedbackStats(BaseModel):
    total: int
    by_label: Dict[str, int]       # Nach Kategorie
    by_model: Dict[str, int] = {}  # Nach Fahrzeugmodell
    by_market: Dict[str, int] = {} # Nach Markt
    by_source: Dict[str, int] = {} # Nach Quelle (voice, touch, error)


@router.get("/", response_model=List[FeedbackItem])
async def list_feedbacks(
    limit: int = 50000,
    label: Optional[str] = None,
    style: Optional[str] = None,
    length_bucket: Optional[str] = None,
    # Legacy Filter
    source_type: Optional[str] = None,
    vehicle_model: Optional[str] = None,
    market: Optional[str] = None
):
    """Alle Feedbacks mit optionalen Filtern."""
    vs = get_vectorstore()
    
    # Alle Dokumente aus ChromaDB abrufen
    try:
        results = vs.collection.get(
            limit=limit,
            include=["documents", "metadatas"]
        )
    except Exception:
        return []
    
    feedbacks = []
    if results and results.get("ids"):
        for i, doc_id in enumerate(results["ids"]):
            meta = results["metadatas"][i] if results.get("metadatas") else {}
            
            # Neue Filter anwenden
            if label and meta.get("label") != label:
                continue
            if style and meta.get("style") != style:
                continue
            if length_bucket and meta.get("length_bucket") != length_bucket:
                continue
            # Legacy Filter
            if source_type and meta.get("source_type") != source_type:
                continue
            if vehicle_model and meta.get("vehicle_model") != vehicle_model:
                continue
            if market and meta.get("market") != market:
                continue
            
            # Confidence aus self_check oder direkt
            confidence = meta.get("confidence", 0.0)
            if isinstance(confidence, str):
                try:
                    confidence = float(confidence)
                except:
                    confidence = 0.0
            
            feedbacks.append(FeedbackItem(
                id=doc_id,
                text=results["documents"][i] if results.get("documents") else "",
                label=meta.get("label", "UNKNOWN"),
                style=meta.get("style", "unknown"),
                length_bucket=meta.get("length_bucket", "medium"),
                confidence=confidence,
                # Legacy
                source_type=meta.get("source_type"),
                language=meta.get("language"),
                timestamp=meta.get("timestamp"),
                vehicle_model=meta.get("vehicle_model"),
                market=meta.get("market")
            ))
    
    return feedbacks


@router.get("/stats", response_model=FeedbackStats)
async def get_stats():
    """Statistiken für Dashboard - angepasst für neuen Datensatz."""
    vs = get_vectorstore()
    
    try:
        results = vs.collection.get(include=["metadatas"])
    except Exception:
        return FeedbackStats(
            total=0,
            by_label={},
            by_style={},
            by_length={},
            by_confidence={}
        )
    
    by_label = {}
    by_style = {}
    by_length = {}
    by_confidence = {"high": 0, "medium": 0, "low": 0}
    # Legacy
    by_source_type = {}
    by_vehicle_model = {}
    by_market = {}
    by_language = {}
    
    if results and results.get("metadatas"):
        for meta in results["metadatas"]:
            # Nach Label (Kategorie)
            label = meta.get("label", "UNKNOWN")
            by_label[label] = by_label.get(label, 0) + 1
            
            # Nach Style
            style = meta.get("style", "unknown")
            by_style[style] = by_style.get(style, 0) + 1
            
            # Nach Length
            length = meta.get("length_bucket", "medium")
            by_length[length] = by_length.get(length, 0) + 1
            
            # Nach Confidence (Buckets)
            conf = meta.get("confidence", 0.0)
            if isinstance(conf, str):
                try:
                    conf = float(conf)
                except:
                    conf = 0.0
            if conf >= 0.8:
                by_confidence["high"] += 1
            elif conf >= 0.6:
                by_confidence["medium"] += 1
            else:
                by_confidence["low"] += 1
            
            # Legacy Felder (falls vorhanden)
            st = meta.get("source_type")
            if st:
                by_source_type[st] = by_source_type.get(st, 0) + 1
            
            vm = meta.get("vehicle_model")
            if vm:
                by_vehicle_model[vm] = by_vehicle_model.get(vm, 0) + 1
            
            mkt = meta.get("market")
            if mkt:
                by_market[mkt] = by_market.get(mkt, 0) + 1
            
            lang = meta.get("language")
            if lang:
                by_language[lang] = by_language.get(lang, 0) + 1
    
    return FeedbackStats(
        total=len(results.get("ids", [])),
        by_label=by_label,
        by_model=by_vehicle_model,
        by_market=by_market,
        by_source=by_source_type
    )


@router.get("/{feedback_id}", response_model=FeedbackItem)
async def get_feedback(feedback_id: str):
    """Einzelnes Feedback abrufen."""
    vs = get_vectorstore()
    
    try:
        results = vs.collection.get(
            ids=[feedback_id],
            include=["documents", "metadatas"]
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Feedback nicht gefunden")
    
    if not results or not results.get("ids"):
        raise HTTPException(status_code=404, detail="Feedback nicht gefunden")
    
    meta = results["metadatas"][0] if results.get("metadatas") else {}
    
    # Confidence
    confidence = meta.get("confidence", 0.0)
    if isinstance(confidence, str):
        try:
            confidence = float(confidence)
        except:
            confidence = 0.0
    
    return FeedbackItem(
        id=feedback_id,
        text=results["documents"][0] if results.get("documents") else "",
        label=meta.get("label", "UNKNOWN"),
        style=meta.get("style", "unknown"),
        length_bucket=meta.get("length_bucket", "medium"),
        confidence=confidence,
        source_type=meta.get("source_type"),
        language=meta.get("language"),
        timestamp=meta.get("timestamp"),
        vehicle_model=meta.get("vehicle_model"),
        market=meta.get("market")
    )
