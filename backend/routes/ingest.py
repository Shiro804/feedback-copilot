"""
Ingest Route - Feedback-Import mit PII-Anonymisierung

Angepasst für den neuen 10K Datensatz mit Feldern:
- label (Kategorie wie NAVIGATION, etc.)
- style (praise, complaint, question, neutral_observation)
- length_bucket (short, medium)
- meta (Generierungs-Infos)
- self_check (predicted_label, is_feedback, confidence)

Literatur:
- Forschungslücke: PII-Anonymisierung in RAG-Pipelines
- Schema-Validierung nach Onepager-Spezifikation
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from services.pii import PIIService
from services.vectorstore import VectorStoreService

router = APIRouter()
pii_service = PIIService()
vectorstore = VectorStoreService()


class FeedbackItem(BaseModel):
    """Angepasst für neuen Datensatz - unterstützt beide Schemata."""
    id: str
    text: str
    # Neues Schema
    label: Optional[str] = None  # Kategorie (NAVIGATION, etc.)
    style: Optional[str] = None  # praise, complaint, etc.
    length_bucket: Optional[str] = None  # short, medium
    confidence: Optional[float] = None  # aus self_check
    # Legacy Schema (für Kompatibilität)
    source_type: Optional[str] = None  # voice, touch, error
    language: Optional[str] = None  # de, en, pl
    timestamp: Optional[str] = None
    vehicle_model: Optional[str] = None
    market: Optional[str] = None
    build_version: Optional[str] = None


class IngestRequest(BaseModel):
    feedbacks: List[FeedbackItem]
    anonymize: bool = True


class PIIResult(BaseModel):
    original_count: int
    anonymized_count: int
    pii_detected: List[dict]


class IngestResponse(BaseModel):
    success: bool
    processed: int
    pii_result: Optional[PIIResult]
    errors: List[str]


@router.post("/", response_model=IngestResponse)
async def ingest_feedbacks(request: IngestRequest):
    """
    Feedback-Daten importieren mit PII-Anonymisierung.
    
    Unterstützt sowohl das neue Schema (label, style, etc.)
    als auch das alte Schema (source_type, vehicle_model, etc.)
    """
    try:
        pii_result = None
        processed_feedbacks = []
        
        for fb in request.feedbacks:
            if request.anonymize:
                # PII-Anonymisierung
                anonymized_text, pii_info = pii_service.anonymize(fb.text)
                fb.text = anonymized_text
            
            processed_feedbacks.append(fb)
        
        # In VectorStore speichern
        await vectorstore.add_documents(processed_feedbacks)
        
        return IngestResponse(
            success=True,
            processed=len(processed_feedbacks),
            pii_result=pii_result,
            errors=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def ingest_stream(
    request: Request,
    anonymize: bool = True
):
    """
    Streaming JSONL-Ingest für Pipeline-Integration.
    
    Empfängt JSONL-Daten als Request Body (nicht File Upload).
    Ideal für Integration mit externem ASR/NLP-Stack.
    
    Akzeptierte Formate:
    1. JSONL (eine JSON pro Zeile):
       {"text": "...", "label": "...", "vehicle_model": "...", ...}
       {"text": "...", "label": "...", "vehicle_model": "...", ...}
    
    2. JSON-Array:
       [{"text": "..."}, {"text": "..."}]
    
    Feldmapping für ASR-Pipeline:
    - transcript → text
    - emotion → style (anger→complaint, joy→praise)
    - intent → label
    - sentiment → sentiment (neu)
    
    Beispiel cURL:
    curl -X POST http://localhost:8000/api/ingest/stream \\
      -H "Content-Type: text/plain" \\
      -d '{"text":"Navigation funktioniert nicht","label":"NAVIGATION"}'
    """
    import json
    from datetime import datetime
    
    content_type = request.headers.get("content-type", "")
    body = await request.body()
    body_str = body.decode("utf-8")
    
    feedbacks = []
    errors = []
    
    try:
        # Versuche als JSON-Array zu parsen
        if "application/json" in content_type or body_str.strip().startswith("["):
            try:
                data = json.loads(body_str)
                if isinstance(data, list):
                    for i, item in enumerate(data):
                        fb = _parse_feedback_item(item, i)
                        if fb:
                            feedbacks.append(fb)
                elif isinstance(data, dict):
                    fb = _parse_feedback_item(data, 0)
                    if fb:
                        feedbacks.append(fb)
            except json.JSONDecodeError as e:
                errors.append(f"JSON Parse Error: {str(e)}")
        else:
            # JSONL-Parsing (eine JSON pro Zeile)
            for i, line in enumerate(body_str.strip().split('\n')):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    fb = _parse_feedback_item(item, i)
                    if fb:
                        feedbacks.append(fb)
                except json.JSONDecodeError as e:
                    if len(errors) < 10:
                        errors.append(f"Zeile {i}: {str(e)}")
        
        if not feedbacks:
            raise HTTPException(status_code=400, detail="Keine gültigen Feedbacks gefunden")
        
        # PII-Anonymisierung und VectorStore
        processed = []
        pii_count = 0
        
        for fb in feedbacks:
            text = fb.get("text", "")
            
            if anonymize:
                anonymized_text, pii_info = pii_service.anonymize(text)
                fb["text"] = anonymized_text
                pii_count += len(pii_info)
            
            # Text mit Metadaten anreichern für bessere Suche
            model = fb.get("vehicle_model", "")
            market = fb.get("market", "")
            source = fb.get("source_type", "voice")
            label = fb.get("label", "")
            
            if model or market or label:
                original_text = fb["text"]
                fb["text"] = f"[{model}] [{market}] [{source}] [{label}] {original_text}"
            
            processed.append(fb)
        
        # In VectorStore speichern
        added = await vectorstore.add_documents(processed)
        
        # Stats berechnen
        stats = {
            "by_label": {},
            "by_model": {},
            "by_market": {},
            "by_source": {}
        }
        for fb in processed:
            for key, stat_key in [("label", "by_label"), ("vehicle_model", "by_model"), 
                                   ("market", "by_market"), ("source_type", "by_source")]:
                if fb.get(key):
                    stats[stat_key][fb[key]] = stats[stat_key].get(fb[key], 0) + 1
        
        return {
            "success": True,
            "processed": added,
            "pii_anonymized": pii_count,
            "errors": errors,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")


def _parse_feedback_item(item: dict, index: int) -> dict:
    """Parse ein Feedback-Item aus verschiedenen Quellformaten."""
    from datetime import datetime
    
    if not item:
        return None
    
    # Text aus verschiedenen Feldern
    text = item.get("text") or item.get("transcript") or item.get("content") or ""
    if not text:
        return None
    
    # ID generieren falls nicht vorhanden
    fb_id = item.get("id") or f"STREAM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{index:04d}"
    
    # Emotion zu Style mapping (für ASR-Pipeline)
    style = item.get("style")
    if not style and item.get("emotion"):
        emotion_map = {
            "anger": "complaint",
            "angry": "complaint", 
            "frustration": "complaint",
            "joy": "praise",
            "happy": "praise",
            "satisfaction": "praise",
            "neutral": "neutral_observation",
            "sadness": "complaint",
            "fear": "complaint"
        }
        style = emotion_map.get(item["emotion"].lower(), "neutral_observation")
    
    # Intent zu Label mapping (falls nötig)
    label = item.get("label") or item.get("category") or item.get("intent")
    
    return {
        "id": fb_id,
        "text": text,
        "label": label,
        "style": style,
        "sentiment": item.get("sentiment"),
        "source_type": item.get("source_type", "voice"),
        "vehicle_model": item.get("vehicle_model"),
        "market": item.get("market"),
        "language": item.get("language", "de"),
        "timestamp": item.get("timestamp") or datetime.now().isoformat(),
        "confidence": item.get("confidence"),
    }


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    CSV/JSON/JSONL-Datei hochladen und verarbeiten.
    
    Unterstützte Formate:
    - JSONL (neues Format): {"id": "...", "text": "...", "label": "...", "style": "...", ...}
    - JSON: Array von Feedback-Objekten
    - CSV: Spalten je nach Schema
    """
    import csv
    import json
    from io import StringIO
    from datetime import datetime
    
    if not file.filename.endswith(('.csv', '.json', '.jsonl')):
        raise HTTPException(status_code=400, detail="Nur CSV/JSON/JSONL erlaubt")
    
    content = await file.read()
    content_str = content.decode("utf-8")
    
    feedbacks = []
    errors = []
    pii_detected_all = []
    
    try:
        if file.filename.endswith('.jsonl'):
            # JSONL-Parsing (eine JSON pro Zeile) - Optimiert für neuen Datensatz
            for i, line in enumerate(content_str.strip().split('\n')):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    
                    # Confidence aus self_check extrahieren
                    confidence = None
                    if "self_check" in item and isinstance(item["self_check"], dict):
                        confidence = item["self_check"].get("confidence")
                    elif "confidence" in item:
                        confidence = item["confidence"]
                    
                    # Timestamp aus meta extrahieren falls vorhanden
                    timestamp = item.get("timestamp")
                    if not timestamp and "meta" in item and isinstance(item["meta"], dict):
                        timestamp = item["meta"].get("generated_at_utc")
                    if not timestamp:
                        timestamp = datetime.now().isoformat()
                    
                    fb = FeedbackItem(
                        id=item.get("id", f"IMPORT-{datetime.now().strftime('%Y%m%d')}-{i:03d}"),
                        text=item.get("text", ""),
                        # Neues Schema
                        label=item.get("label"),
                        style=item.get("style"),
                        length_bucket=item.get("length_bucket"),
                        confidence=confidence,
                        # Legacy Schema
                        source_type=item.get("source_type"),
                        language=item.get("language", "en"),
                        timestamp=timestamp,
                        vehicle_model=item.get("vehicle_model"),
                        market=item.get("market"),
                        build_version=item.get("build_version")
                    )
                    feedbacks.append(fb)
                except Exception as e:
                    if i < 10:  # Nur erste 10 Fehler loggen
                        errors.append(f"Zeile {i}: {str(e)}")
                        
        elif file.filename.endswith('.json'):
            # JSON-Parsing
            data = json.loads(content_str)
            if isinstance(data, list):
                for i, item in enumerate(data):
                    try:
                        # Confidence extrahieren
                        confidence = None
                        if "self_check" in item and isinstance(item["self_check"], dict):
                            confidence = item["self_check"].get("confidence")
                        elif "confidence" in item:
                            confidence = item["confidence"]
                        
                        fb = FeedbackItem(
                            id=item.get("id", f"IMPORT-{datetime.now().strftime('%Y%m%d')}-{i:03d}"),
                            text=item.get("text", ""),
                            label=item.get("label"),
                            style=item.get("style"),
                            length_bucket=item.get("length_bucket"),
                            confidence=confidence,
                            source_type=item.get("source_type"),
                            language=item.get("language", "de"),
                            timestamp=item.get("timestamp", datetime.now().isoformat()),
                            vehicle_model=item.get("vehicle_model"),
                            market=item.get("market"),
                            build_version=item.get("build_version")
                        )
                        feedbacks.append(fb)
                    except Exception as e:
                        if i < 10:
                            errors.append(f"Zeile {i}: {str(e)}")
        else:
            # CSV-Parsing
            reader = csv.DictReader(StringIO(content_str))
            for i, row in enumerate(reader):
                try:
                    # Confidence parsen
                    confidence = None
                    if row.get("confidence"):
                        try:
                            confidence = float(row["confidence"])
                        except:
                            pass
                    
                    fb = FeedbackItem(
                        id=row.get("id", f"IMPORT-{datetime.now().strftime('%Y%m%d')}-{i:03d}"),
                        text=row.get("text", ""),
                        label=row.get("label"),
                        style=row.get("style"),
                        length_bucket=row.get("length_bucket"),
                        confidence=confidence,
                        source_type=row.get("source_type"),
                        language=row.get("language", "de"),
                        timestamp=row.get("timestamp", datetime.now().isoformat()),
                        vehicle_model=row.get("vehicle_model"),
                        market=row.get("market"),
                        build_version=row.get("build_version")
                    )
                    feedbacks.append(fb)
                except Exception as e:
                    if i < 10:
                        errors.append(f"Zeile {i}: {str(e)}")
        
        # PII-Erkennung und Anonymisierung
        processed_feedbacks = []
        for fb in feedbacks:
            # PII erkennen (für Preview)
            detected = pii_service.detect_only(fb.text)
            pii_detected_all.extend(detected)
            
            # Anonymisieren
            anonymized_text, pii_info = pii_service.anonymize(fb.text)
            
            # Neues Feedback-Dict mit anonymisiertem Text und beiden Schemata
            doc = {
                "id": fb.id,
                "text": anonymized_text,
            }
            
            # Neue Felder hinzufügen (wenn vorhanden)
            if fb.label:
                doc["label"] = fb.label
            if fb.style:
                doc["style"] = fb.style
            if fb.length_bucket:
                doc["length_bucket"] = fb.length_bucket
            if fb.confidence is not None:
                doc["confidence"] = fb.confidence
            
            # Legacy Felder hinzufügen (wenn vorhanden)
            if fb.source_type:
                doc["source_type"] = fb.source_type
            if fb.language:
                doc["language"] = fb.language
            if fb.timestamp:
                doc["timestamp"] = fb.timestamp
            if fb.vehicle_model:
                doc["vehicle_model"] = fb.vehicle_model
            if fb.market:
                doc["market"] = fb.market
            
            processed_feedbacks.append(doc)
        
        # In VectorStore speichern
        await vectorstore.add_documents(processed_feedbacks)
        
        # Stats berechnen - VW-spezifisch
        label_stats = {}
        model_stats = {}
        market_stats = {}
        source_stats = {}
        for fb in feedbacks:
            if fb.label:
                label_stats[fb.label] = label_stats.get(fb.label, 0) + 1
            if fb.vehicle_model:
                model_stats[fb.vehicle_model] = model_stats.get(fb.vehicle_model, 0) + 1
            if fb.market:
                market_stats[fb.market] = market_stats.get(fb.market, 0) + 1
            if fb.source_type:
                source_stats[fb.source_type] = source_stats.get(fb.source_type, 0) + 1
        
        return {
            "success": True,
            "filename": file.filename,
            "processed": len(processed_feedbacks),
            "errors": errors[:10],
            "pii_detected": pii_detected_all[:50],
            "pii_summary": {
                "total_found": len(pii_detected_all),
                "by_type": {}
            },
            "stats": {
                "by_label": label_stats,
                "by_model": model_stats,
                "by_market": market_stats,
                "by_source": source_stats
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Verarbeiten: {str(e)}")


@router.post("/load-dataset")
async def load_dataset_file(dataset_path: str = "api/dataset.jsonl"):
    """
    Lädt den 10K Datensatz direkt aus der Datei.
    Optimiert für den neuen Datensatz mit label, style, etc.
    """
    import json
    from pathlib import Path
    
    # Pfad relativ zum Backend-Verzeichnis
    path = Path(__file__).parent.parent / dataset_path
    
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Datei nicht gefunden: {dataset_path}")
    
    feedbacks = []
    errors = []
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    
                    # Confidence aus self_check
                    confidence = None
                    if "self_check" in item:
                        confidence = item["self_check"].get("confidence")
                    
                    doc = {
                        "id": item.get("id", f"DS-{i:05d}"),
                        "text": item.get("text", ""),
                        "label": item.get("label"),
                        "style": item.get("style"),
                        "length_bucket": item.get("length_bucket"),
                        "confidence": confidence,
                    }
                    feedbacks.append(doc)
                except Exception as e:
                    if len(errors) < 10:
                        errors.append(f"Zeile {i}: {str(e)}")
        
        # In VectorStore speichern
        await vectorstore.add_documents(feedbacks)
        
        return {
            "success": True,
            "processed": len(feedbacks),
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")


@router.get("/status")
async def ingest_status():
    """Status des Ingest-Prozesses abrufen."""
    return {
        "total_documents": await vectorstore.count(),
        "last_ingest": None,
        "pii_enabled": True
    }


@router.post("/clear-and-reload")
async def clear_and_reload_dataset():
    """
    Löscht alle existierenden Dokumente und lädt den 10K Datensatz neu.
    Bevorzugt enriched Dataset mit VW-spezifischen Feldern.
    ACHTUNG: Dies löscht alle Daten!
    """
    import json
    from pathlib import Path
    
    # Bevorzuge enriched Dataset
    enriched_path = Path(__file__).parent.parent / "api" / "dataset_enriched.jsonl"
    fallback_path = Path(__file__).parent.parent / "api" / "dataset.jsonl"
    dataset_path = enriched_path if enriched_path.exists() else fallback_path
    
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail=f"Datei nicht gefunden: {dataset_path}")
    
    # 1. Alle existierenden Dokumente löschen
    try:
        existing = vectorstore.collection.get()
        if existing and existing.get("ids"):
            old_count = len(existing["ids"])
            # In Batches löschen (ChromaDB Limit)
            batch_size = 5000
            for i in range(0, len(existing["ids"]), batch_size):
                batch_ids = existing["ids"][i:i + batch_size]
                vectorstore.collection.delete(ids=batch_ids)
            print(f"🗑️ {old_count} alte Dokumente gelöscht")
    except Exception as e:
        print(f"⚠️ Fehler beim Löschen: {e}")
    
    # 2. Neuen Datensatz laden
    feedbacks = []
    errors = []
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                
                # Unterstütze beide Formate (enriched und alt)
                if "vehicle_model" in item:
                    # Enriched Format mit VW-Feldern
                    # Text mit Metadaten-Prefix für bessere semantische Suche
                    original_text = item.get("text", "")
                    model = item.get("vehicle_model", "")
                    market = item.get("market", "")
                    source = item.get("source_type", "")
                    label = item.get("label", "")
                    
                    # Enriched text: [Modell] [Markt] [Quelle] [Kategorie] Original-Text
                    enriched_text = f"[{model}] [{market}] [{source}] [{label}] {original_text}"
                    
                    doc = {
                        "id": item.get("id", f"DS-{i:05d}"),
                        "text": enriched_text,
                        "label": label,
                        "style": item.get("style"),
                        "length_bucket": item.get("length_bucket"),
                        "vehicle_model": model,
                        "market": market,
                        "vin": item.get("vin"),
                        "language": item.get("language"),
                        "source_type": source,
                        "timestamp": item.get("timestamp"),
                        "confidence": item.get("confidence", 0.8),
                    }
                else:
                    # Altes Format (Fallback)
                    confidence = None
                    if "self_check" in item and isinstance(item["self_check"], dict):
                        confidence = item["self_check"].get("confidence")
                    
                    doc = {
                        "id": item.get("id", f"DS-{i:05d}"),
                        "text": item.get("text", ""),
                        "label": item.get("label"),
                        "style": item.get("style"),
                        "length_bucket": item.get("length_bucket"),
                        "confidence": confidence,
                    }
                feedbacks.append(doc)
            except Exception as e:
                if len(errors) < 10:
                    errors.append(f"Zeile {i}: {str(e)}")
    
    # 3. In Batches zum VectorStore hinzufügen
    batch_size = 1000
    total_added = 0
    
    for i in range(0, len(feedbacks), batch_size):
        batch = feedbacks[i:i + batch_size]
        added = await vectorstore.add_documents(batch)
        total_added += added
        print(f"✅ Batch {i // batch_size + 1}: {added} Dokumente")
    
    # Stats berechnen
    label_stats = {}
    style_stats = {}
    model_stats = {}
    market_stats = {}
    source_stats = {}
    
    for fb in feedbacks:
        if fb.get("label"):
            label_stats[fb["label"]] = label_stats.get(fb["label"], 0) + 1
        if fb.get("style"):
            style_stats[fb["style"]] = style_stats.get(fb["style"], 0) + 1
        if fb.get("vehicle_model"):
            model_stats[fb["vehicle_model"]] = model_stats.get(fb["vehicle_model"], 0) + 1
        if fb.get("market"):
            market_stats[fb["market"]] = market_stats.get(fb["market"], 0) + 1
        if fb.get("source_type"):
            source_stats[fb["source_type"]] = source_stats.get(fb["source_type"], 0) + 1
    
    return {
        "success": True,
        "loaded": total_added,
        "dataset_used": str(dataset_path),
        "errors": errors,
        "stats": {
            "by_label": dict(sorted(label_stats.items(), key=lambda x: -x[1])[:5]),
            "by_style": style_stats,
            "by_model": dict(sorted(model_stats.items(), key=lambda x: -x[1])[:5]),
            "by_market": dict(sorted(market_stats.items(), key=lambda x: -x[1])[:5]),
            "by_source": source_stats
        }
    }
