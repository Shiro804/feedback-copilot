"""
Script zum Erweitern des 10K Datensatzes mit VW-spezifischen Feldern.
Fügt hinzu: vehicle_model, market, vin, language, source_type, timestamp
"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

# Pfade
BACKEND_DIR = Path(__file__).parent
INPUT_PATH = BACKEND_DIR / "api" / "dataset.jsonl"
OUTPUT_PATH = BACKEND_DIR / "api" / "dataset_enriched.jsonl"

# VW-spezifische Werte
VW_MODELS = [
    "ID.3", "ID.4", "ID.5", "ID.7",  # E-Autos
    "Golf 8", "Golf GTE", 
    "Passat", "Passat Variant",
    "Tiguan", "Tiguan Allspace",
    "Touareg",
    "Polo", "T-Cross", "T-Roc",
    "Arteon", "Taigo"
]

# Gewichtung: ID.-Modelle häufiger (E-Auto Fokus)
MODEL_WEIGHTS = {
    "ID.3": 15, "ID.4": 20, "ID.5": 8, "ID.7": 5,
    "Golf 8": 12, "Golf GTE": 4,
    "Passat": 6, "Passat Variant": 4,
    "Tiguan": 8, "Tiguan Allspace": 3,
    "Touareg": 3,
    "Polo": 5, "T-Cross": 3, "T-Roc": 4,
    "Arteon": 2, "Taigo": 2
}

MARKETS = {
    "DE": 40,  # Deutschland häufigster Markt
    "AT": 8,
    "CH": 6,
    "NL": 5,
    "BE": 4,
    "FR": 8,
    "UK": 10,
    "US": 8,
    "CN": 7,
    "NO": 4  # E-Auto Vorreiter
}

LANGUAGES = {
    "de": 50,  # Deutsch dominant
    "en": 40,
    "fr": 5,
    "nl": 3,
    "zh": 2
}

SOURCE_TYPES = {
    "voice": 45,   # Sprachassistent Feedback
    "touch": 35,   # Touchscreen Feedback
    "error": 15,   # Fehlermeldungen
    "survey": 5    # Umfragen
}


def weighted_choice(options: dict) -> str:
    """Wählt ein Element basierend auf Gewichtung."""
    items = list(options.keys())
    weights = list(options.values())
    return random.choices(items, weights=weights, k=1)[0]


def generate_vin(model: str) -> str:
    """
    Generiert eine VW-ähnliche VIN (17 Zeichen).
    Format: WVW + ZZZ + Model-Code + Seriennummer
    """
    # WVW = Volkswagen
    prefix = "WVW"
    # Placeholder für Fahrzeugklasse
    filler = "ZZZ"
    # Model-Code (2 Zeichen basierend auf Modell)
    model_codes = {
        "ID.3": "E1", "ID.4": "E2", "ID.5": "E3", "ID.7": "E4",
        "Golf 8": "AU", "Golf GTE": "BE",
        "Passat": "3C", "Passat Variant": "3G",
        "Tiguan": "AD", "Tiguan Allspace": "BW",
        "Touareg": "CR", "Polo": "AW", "T-Cross": "C1",
        "T-Roc": "A1", "Arteon": "3H", "Taigo": "CS"
    }
    model_code = model_codes.get(model, "XX")
    # 8 zufällige alphanumerische Zeichen
    chars = "0123456789ABCDEFGHJKLMNPRSTUVWXYZ"  # Keine I, O, Q
    serial = ''.join(random.choices(chars, k=8))
    
    return f"{prefix}{filler}{model_code}{serial}"


def generate_timestamp() -> str:
    """Generiert einen zufälligen Timestamp der letzten 6 Monate."""
    now = datetime.now()
    days_ago = random.randint(0, 180)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    
    dt = now - timedelta(days=days_ago, hours=hours, minutes=minutes)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def enrich_feedback(item: dict) -> dict:
    """Erweitert einen Feedback-Eintrag mit VW-spezifischen Feldern."""
    # Modell auswählen
    model = weighted_choice(MODEL_WEIGHTS)
    
    # Restliche Felder
    market = weighted_choice(MARKETS)
    language = weighted_choice(LANGUAGES)
    source_type = weighted_choice(SOURCE_TYPES)
    
    # VIN generieren
    vin = generate_vin(model)
    
    # Timestamp
    timestamp = generate_timestamp()
    
    # Enriched item erstellen
    enriched = {
        "id": item.get("id"),
        "text": item.get("text"),
        "label": item.get("label"),
        "style": item.get("style"),
        "length_bucket": item.get("length_bucket"),
        "vehicle_model": model,
        "market": market,
        "vin": vin,
        "language": language,
        "source_type": source_type,
        "timestamp": timestamp,
        "confidence": item.get("self_check", {}).get("confidence", 0.8)
    }
    
    return enriched


def main():
    print(f"📂 Lade Datensatz: {INPUT_PATH}")
    
    if not INPUT_PATH.exists():
        print(f"❌ Datei nicht gefunden: {INPUT_PATH}")
        return
    
    enriched_items = []
    
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                enriched = enrich_feedback(item)
                enriched_items.append(enriched)
                
                if (i + 1) % 1000 == 0:
                    print(f"  📝 {i + 1} Einträge verarbeitet...")
                    
            except Exception as e:
                print(f"  ⚠️ Zeile {i}: {e}")
    
    print(f"✅ {len(enriched_items)} Einträge erweitert")
    
    # Speichern
    print(f"💾 Speichere nach: {OUTPUT_PATH}")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for item in enriched_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    # Statistiken
    print("\n📊 Statistiken:")
    
    # Models
    models = {}
    markets = {}
    sources = {}
    for item in enriched_items:
        m = item["vehicle_model"]
        models[m] = models.get(m, 0) + 1
        
        mk = item["market"]
        markets[mk] = markets.get(mk, 0) + 1
        
        s = item["source_type"]
        sources[s] = sources.get(s, 0) + 1
    
    print(f"  Modelle (Top 5): {dict(sorted(models.items(), key=lambda x: -x[1])[:5])}")
    print(f"  Märkte: {dict(sorted(markets.items(), key=lambda x: -x[1])[:5])}")
    print(f"  Quellen: {sources}")
    
    print(f"\n🎉 Fertig! Datei gespeichert: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
