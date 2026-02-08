"""
Script zum Laden des 10K Datensatzes in den VectorStore.
Löscht zuerst den alten VectorStore und lädt alle Daten neu.
"""

import asyncio
import json
from pathlib import Path
import shutil

# Pfade
BACKEND_DIR = Path(__file__).parent
DATASET_PATH = BACKEND_DIR / "api" / "dataset_enriched.jsonl"  # Nutze angereicherten Datensatz
FALLBACK_PATH = BACKEND_DIR / "api" / "dataset.jsonl"  # Fallback wenn enriched nicht existiert
CHROMA_DIR = BACKEND_DIR / "chroma_db"


async def main():
    # 1. Alten VectorStore löschen
    if CHROMA_DIR.exists():
        print(f"🗑️  Lösche alten VectorStore: {CHROMA_DIR}")
        shutil.rmtree(CHROMA_DIR)
        print("✅ Alter VectorStore gelöscht")
    
    # 2. VectorStore neu initialisieren
    from services.vectorstore import VectorStoreService
    vs = VectorStoreService()
    print(f"📦 Neuer VectorStore initialisiert")
    
    # 3. Datensatz laden (bevorzuge enriched)
    dataset_path = DATASET_PATH if DATASET_PATH.exists() else FALLBACK_PATH
    print(f"📂 Lade Datensatz: {dataset_path}")
    
    if not dataset_path.exists():
        print(f"❌ Datei nicht gefunden: {dataset_path}")
        return
    
    feedbacks = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                
                # Unterstütze beide Formate (alt und enriched)
                if "vehicle_model" in item:
                    # Neues enriched Format
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
                
                # Progress anzeigen
                if (i + 1) % 1000 == 0:
                    print(f"  📝 {i + 1} Zeilen gelesen...")
                    
            except Exception as e:
                print(f"  ⚠️ Zeile {i}: {e}")
    
    print(f"📊 {len(feedbacks)} Feedbacks geladen")
    
    # 4. In Batches zum VectorStore hinzufügen (ChromaDB hat Batch-Limits)
    BATCH_SIZE = 1000
    total_added = 0
    
    for i in range(0, len(feedbacks), BATCH_SIZE):
        batch = feedbacks[i:i + BATCH_SIZE]
        added = await vs.add_documents(batch)
        total_added += added
        print(f"  ✅ Batch {i // BATCH_SIZE + 1}: {added} Dokumente hinzugefügt (Gesamt: {total_added})")
    
    # 5. Verifizieren
    count = await vs.count()
    print(f"\n🎉 Fertig! VectorStore enthält jetzt {count} Dokumente")
    
    # Stats anzeigen
    results = vs.collection.get(include=["metadatas"], limit=10000)
    if results and results.get("metadatas"):
        labels = {}
        styles = {}
        models = {}
        markets = {}
        sources = {}
        
        for meta in results["metadatas"]:
            label = meta.get("label", "UNKNOWN")
            style = meta.get("style", "unknown")
            model = meta.get("vehicle_model", "unknown")
            market = meta.get("market", "unknown")
            source = meta.get("source_type", "unknown")
            
            labels[label] = labels.get(label, 0) + 1
            styles[style] = styles.get(style, 0) + 1
            models[model] = models.get(model, 0) + 1
            markets[market] = markets.get(market, 0) + 1
            sources[source] = sources.get(source, 0) + 1
        
        print("\n📈 Statistiken:")
        print("  Labels:", dict(sorted(labels.items(), key=lambda x: -x[1])[:5]))
        print("  Styles:", dict(sorted(styles.items(), key=lambda x: -x[1])[:5]))
        print("  Modelle (Top 5):", dict(sorted(models.items(), key=lambda x: -x[1])[:5]))
        print("  Märkte (Top 5):", dict(sorted(markets.items(), key=lambda x: -x[1])[:5]))
        print("  Quellen:", sources)


if __name__ == "__main__":
    asyncio.run(main())
