"""
Export Route - Datenexport in verschiedenen Formaten

Features:
- CSV Export
- JSON Export  
- JSONL Export
- PDF Export (mit reportlab)

Alle Exporte enthalten die VW-spezifischen Felder:
- vehicle_model, market, vin, language, source_type, timestamp
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
import json
import io
import csv
from datetime import datetime

# PDF-Bibliothek
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from services.vectorstore import VectorStoreService

router = APIRouter()
vectorstore = VectorStoreService()


def get_all_feedbacks(
    label: Optional[str] = None,
    style: Optional[str] = None,
    market: Optional[str] = None,
    vehicle_model: Optional[str] = None,
    source_type: Optional[str] = None,
    limit: int = 50000
) -> List[dict]:
    """Lade alle Feedbacks mit optionalen Filtern."""
    results = vectorstore.collection.get(
        include=["documents", "metadatas"],
        limit=limit
    )
    
    if not results or not results.get("ids"):
        return []
    
    feedbacks = []
    for i, doc_id in enumerate(results["ids"]):
        meta = results["metadatas"][i] if results.get("metadatas") else {}
        text = results["documents"][i] if results.get("documents") else ""
        
        # Filter anwenden
        if label and meta.get("label") != label:
            continue
        if style and meta.get("style") != style:
            continue
        if market and meta.get("market") != market:
            continue
        if vehicle_model and meta.get("vehicle_model") != vehicle_model:
            continue
        if source_type and meta.get("source_type") != source_type:
            continue
        
        feedback = {
            "id": doc_id,
            "text": text,
            "label": meta.get("label", ""),
            "style": meta.get("style", ""),
            "length_bucket": meta.get("length_bucket", ""),
            "confidence": meta.get("confidence", 0.0),
            "vehicle_model": meta.get("vehicle_model", ""),
            "market": meta.get("market", ""),
            "vin": meta.get("vin", ""),
            "language": meta.get("language", ""),
            "source_type": meta.get("source_type", ""),
            "timestamp": meta.get("timestamp", "")
        }
        feedbacks.append(feedback)
    
    return feedbacks


@router.get("/csv")
async def export_csv(
    label: Optional[str] = None,
    style: Optional[str] = None,
    market: Optional[str] = None,
    vehicle_model: Optional[str] = None,
    source_type: Optional[str] = None
):
    """Export als CSV-Datei."""
    feedbacks = get_all_feedbacks(label, style, market, vehicle_model, source_type)
    
    if not feedbacks:
        raise HTTPException(status_code=404, detail="Keine Feedbacks gefunden")
    
    # CSV erstellen
    output = io.StringIO()
    fieldnames = [
        "id", "text", "label", "style", "length_bucket", "confidence",
        "vehicle_model", "market", "vin", "language", "source_type", "timestamp"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(feedbacks)
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),  # BOM für Excel
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=feedbacks.csv"}
    )


@router.get("/json")
async def export_json(
    label: Optional[str] = None,
    style: Optional[str] = None,
    market: Optional[str] = None,
    vehicle_model: Optional[str] = None,
    source_type: Optional[str] = None
):
    """Export als JSON-Array."""
    feedbacks = get_all_feedbacks(label, style, market, vehicle_model, source_type)
    
    if not feedbacks:
        raise HTTPException(status_code=404, detail="Keine Feedbacks gefunden")
    
    output = json.dumps(feedbacks, ensure_ascii=False, indent=2)
    
    return StreamingResponse(
        io.BytesIO(output.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=feedbacks.json"}
    )


@router.get("/jsonl")
async def export_jsonl(
    label: Optional[str] = None,
    style: Optional[str] = None,
    market: Optional[str] = None,
    vehicle_model: Optional[str] = None,
    source_type: Optional[str] = None
):
    """Export als JSONL (eine JSON pro Zeile)."""
    feedbacks = get_all_feedbacks(label, style, market, vehicle_model, source_type)
    
    if not feedbacks:
        raise HTTPException(status_code=404, detail="Keine Feedbacks gefunden")
    
    lines = [json.dumps(fb, ensure_ascii=False) for fb in feedbacks]
    output = "\n".join(lines)
    
    return StreamingResponse(
        io.BytesIO(output.encode('utf-8')),
        media_type="application/jsonl",
        headers={"Content-Disposition": "attachment; filename=feedbacks.jsonl"}
    )


@router.get("/stats")
async def export_stats():
    """Export-Statistiken: Anzahl der Feedbacks nach Filtern."""
    results = vectorstore.collection.get(include=["metadatas"], limit=10000)
    
    if not results or not results.get("metadatas"):
        return {"total": 0, "by_label": {}, "by_market": {}, "by_model": {}}
    
    from collections import Counter
    
    labels = Counter()
    markets = Counter()
    models = Counter()
    sources = Counter()
    
    for meta in results["metadatas"]:
        if meta.get("label"):
            labels[meta["label"]] += 1
        if meta.get("market"):
            markets[meta["market"]] += 1
        if meta.get("vehicle_model"):
            models[meta["vehicle_model"]] += 1
        if meta.get("source_type"):
            sources[meta["source_type"]] += 1
    
    return {
        "total": len(results["metadatas"]),
        "by_label": dict(labels),
        "by_market": dict(markets),
        "by_model": dict(models),
        "by_source": dict(sources)
    }


@router.get("/pdf")
async def export_pdf(
    label: Optional[List[str]] = Query(None),
    market: Optional[List[str]] = Query(None),
    vehicle_model: Optional[List[str]] = Query(None),
    source_type: Optional[List[str]] = Query(None),
    limit: int = 500
):
    """Export als PDF-Report mit professionellem Layout."""
    if not PDF_AVAILABLE:
        raise HTTPException(
            status_code=501, 
            detail="PDF-Export nicht verfügbar. Bitte 'pip install reportlab' ausführen."
        )
    
    # Alle Feedbacks laden
    all_feedbacks = get_all_feedbacks(limit=10000)
    
    # Filter anwenden (multiple Werte möglich)
    filtered = all_feedbacks
    if label:
        filtered = [fb for fb in filtered if fb.get("label") in label]
    if market:
        filtered = [fb for fb in filtered if fb.get("market") in market]
    if vehicle_model:
        filtered = [fb for fb in filtered if fb.get("vehicle_model") in vehicle_model]
    if source_type:
        filtered = [fb for fb in filtered if fb.get("source_type") in source_type]
    
    feedbacks = filtered[:limit]
    
    if not feedbacks:
        raise HTTPException(status_code=404, detail="Keine Feedbacks gefunden")
    
    # PDF erstellen
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Header
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.HexColor('#1a365d')
    )
    elements.append(Paragraph("Feedback-Copilot: Datenexport", title_style))
    
    # Infos
    info_style = styles['Normal']
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    filter_info = []
    if label:
        filter_info.append(f"Label: {label}")
    if market:
        filter_info.append(f"Markt: {market}")
    if vehicle_model:
        filter_info.append(f"Modell: {vehicle_model}")
    if source_type:
        filter_info.append(f"Quelle: {source_type}")
    
    elements.append(Paragraph(
        f"Erstellt: {now} | Anzahl: {len(feedbacks)} | "
        f"Filter: {', '.join(filter_info) if filter_info else 'Keine'}",
        info_style
    ))
    elements.append(Spacer(1, 20))
    
    # Tabelle erstellen - Text als Paragraph für automatischen Zeilenumbruch
    table_data = [["ID", "Modell", "Markt", "Kategorie", "Feedback-Text"]]
    
    text_style = ParagraphStyle(
        'TableText',
        fontSize=7,
        leading=9,
        fontName='Helvetica'
    )
    
    for fb in feedbacks:
        text = fb.get("text", "")
        # Text als Paragraph für automatischen Zeilenumbruch
        text_para = Paragraph(text.replace("<", "&lt;").replace(">", "&gt;"), text_style)
        table_data.append([
            fb.get("id", "")[:12],
            fb.get("vehicle_model", ""),
            fb.get("market", ""),
            fb.get("label", ""),
            text_para  # Voller Text mit Umbruch
        ])
    
    # Tabelle formatieren
    col_widths = [2.5*cm, 2.5*cm, 2*cm, 3*cm, 15*cm]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Body
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#edf2f7')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]))
    
    elements.append(table)
    
    # Footer
    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray
    )
    elements.append(Paragraph(
        "Generiert vom Feedback-Copilot | Volkswagen RAG-Pipeline | Master-Thesis Selim Semir",
        footer_style
    ))
    
    # PDF generieren
    doc.build(elements)
    buffer.seek(0)
    
    # Dateiname mit Zeitstempel
    filename = f"feedbacks_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
