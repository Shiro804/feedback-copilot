"""
Testdaten für Feedback-Copilot

Lädt die 10.000 synthetischen Intent-Testdaten aus dem JSONL-Dataset.
Ersetzt die bisherigen 40 Mockdaten.

Dataset: intent_dataset_clean_first6.jsonl
Format: JSONL (eine JSON pro Zeile)
"""

import asyncio
import json
import os
from services.vectorstore import VectorStoreService

# Pfad zur JSONL-Datei (mit eindeutigen IDs)
DATASET_PATH = os.path.join(os.path.dirname(__file__), "api", "dataset.jsonl")


def load_jsonl_dataset(filepath: str, limit: int = None) -> list:
    """
    JSONL-Dataset laden und in VectorStore-Format konvertieren.
    
    JSONL-Schema:
    {
        "id": "NAV_0001",
        "text": "...",
        "label": "NAVIGATION",
        "style": "complaint",
        "length_bucket": "medium",
        "meta": {"generated_at_utc": "..."},
        ...
    }
    
    VectorStore-Schema:
    {
        "id": "...",
        "text": "...",
        "source_type": "navigation",  # label -> lowercase
        "language": "en",              # Standard: en
        "timestamp": "...",            # aus meta.generated_at_utc
        "vehicle_model": None,
        "market": None
    }
    """
    feedbacks = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
                
            try:
                item = json.loads(line.strip())
                
                # Mapping - IDs sind jetzt eindeutig im neuen Dataset
                feedback = {
                    "id": item.get("id"),
                    "text": item.get("text", ""),
                    "source_type": item.get("label", "unknown").lower(),
                    "language": "en",  # Dataset ist englisch
                    "timestamp": item.get("meta", {}).get("generated_at_utc", ""),
                    "vehicle_model": "",  # Nicht im Dataset
                    "market": ""  # Nicht im Dataset
                }
                
                # Style als zusätzliche Info (complaint, praise, question etc.)
                style = item.get("style", "")
                if style:
                    feedback["style"] = style
                    
                feedbacks.append(feedback)
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Zeile {i} übersprungen: {e}")
                continue
    
    return feedbacks


async def seed_test_data(limit: int = None, force: bool = False):
    """
    Testdaten in VectorStore laden.
    
    Args:
        limit: Optional - Anzahl der Einträge limitieren (für schnelle Tests)
        force: Falls True, vorhandene Daten werden überschrieben
    """
    print("🚀 Lade Testdaten aus JSONL...")
    
    if not os.path.exists(DATASET_PATH):
        print(f"❌ Dataset nicht gefunden: {DATASET_PATH}")
        return
    
    vs = VectorStoreService()
    
    # Prüfen ob schon Daten vorhanden
    count = await vs.count()
    if count > 0 and not force:
        print(f"⚠️  VectorStore enthält bereits {count} Dokumente.")
        print("   Nutze --force um zu überschreiben.")
        print("   Überspringe Seeding.")
        return
    
    # Dataset laden
    print(f"📂 Lade Dataset: {DATASET_PATH}")
    feedbacks = load_jsonl_dataset(DATASET_PATH, limit=limit)
    print(f"📊 {len(feedbacks)} Einträge geladen")
    
    # Labels/Kategorien anzeigen
    labels = {}
    for fb in feedbacks:
        label = fb.get("source_type", "unknown")
        labels[label] = labels.get(label, 0) + 1
    
    print("\n📈 Verteilung nach Kategorie:")
    for label, count in sorted(labels.items(), key=lambda x: -x[1]):
        print(f"   {label}: {count}")
    
    # In VectorStore speichern (in Batches wegen ChromaDB Limit)
    print("\n💾 Speichere in VectorStore...")
    BATCH_SIZE = 5000  # ChromaDB max is 5461
    
    for i in range(0, len(feedbacks), BATCH_SIZE):
        batch = feedbacks[i:i + BATCH_SIZE]
        await vs.add_documents(batch)
        print(f"   Batch {i // BATCH_SIZE + 1}: {len(batch)} Einträge gespeichert")
    
    new_count = await vs.count()
    print(f"\n✅ {new_count} Feedbacks geladen!")
    print("\nBeispiel-Fragen zum Testen:")
    print("  - What are the main navigation issues?")
    print("  - Show me complaints about voice control")
    print("  - What positive feedback exists?")


if __name__ == "__main__":
    import sys
    
    limit = None
    force = False
    
    # CLI-Argumente parsen
    for arg in sys.argv[1:]:
        if arg == "--force":
            force = True
        elif arg.startswith("--limit="):
            try:
                limit = int(arg.split("=")[1])
            except ValueError:
                print(f"Ungültiges Limit: {arg}")
                sys.exit(1)
    
    asyncio.run(seed_test_data(limit=limit, force=force))
