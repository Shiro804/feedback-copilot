"""
Demo-Daten für Feedback-Copilot

40 Synthetische In-Car Feedbackdaten:
- Sprachassistenz-Transkripte
- Touch-Event-Logs
- Fehlermeldungen

Mehrsprachig: DE/EN
Fahrzeugmodelle: ID.4, ID.5, Golf 8, Passat, Tiguan
Märkte: DE, AT, CH, UK, PL
"""

import asyncio
from services.vectorstore import VectorStoreService

# Synthetische Demo-Feedbacks (40 Einträge)
DEMO_FEEDBACKS = [
    # ============ SPRACHASSISTENT (12 Einträge) ============
    {
        "id": "FB-2026-001",
        "text": "Der Sprachassistent versteht mich nicht richtig. Ich sage 'Navigiere nach Berlin' aber er sucht nach 'Perlin'. Das passiert sehr oft.",
        "source_type": "voice",
        "language": "de",
        "timestamp": "2026-01-10T08:15:00Z",
        "vehicle_model": "ID.4",
        "market": "DE"
    },
    {
        "id": "FB-2026-002",
        "text": "Sprachsteuerung für Klimaanlage funktioniert nicht. Sage 'Temperatur auf 22 Grad' und nichts passiert.",
        "source_type": "voice",
        "language": "de",
        "timestamp": "2026-01-10T09:30:00Z",
        "vehicle_model": "ID.5",
        "market": "DE"
    },
    {
        "id": "FB-2026-003",
        "text": "Voice assistant doesn't understand English commands properly. Navigation requests are often misinterpreted.",
        "source_type": "voice",
        "language": "en",
        "timestamp": "2026-01-10T10:00:00Z",
        "vehicle_model": "ID.4",
        "market": "UK"
    },
    {
        "id": "FB-2026-004",
        "text": "Hey Volkswagen Befehl wird nicht erkannt. Muss mehrmals wiederholen bis das System reagiert.",
        "source_type": "voice",
        "language": "de",
        "timestamp": "2026-01-10T11:20:00Z",
        "vehicle_model": "Golf 8",
        "market": "DE"
    },
    {
        "id": "FB-2026-005",
        "text": "Sprachassistent bricht mitten im Satz ab. Sehr frustrierend wenn man längere Adressen eingeben will.",
        "source_type": "voice",
        "language": "de",
        "timestamp": "2026-01-10T14:45:00Z",
        "vehicle_model": "ID.4",
        "market": "AT"
    },
    {
        "id": "FB-2026-006",
        "text": "Sprachassistent versteht Dialekt nicht. Muss Hochdeutsch sprechen damit er funktioniert.",
        "source_type": "voice",
        "language": "de",
        "timestamp": "2026-01-10T15:30:00Z",
        "vehicle_model": "Tiguan",
        "market": "AT"
    },
    {
        "id": "FB-2026-007",
        "text": "Nach dem Update reagiert der Sprachassistent viel schneller. Sehr positiv!",
        "source_type": "voice",
        "language": "de",
        "timestamp": "2026-01-10T16:00:00Z",
        "vehicle_model": "ID.5",
        "market": "CH"
    },
    {
        "id": "FB-2026-008",
        "text": "Voice control for music works perfectly. Love saying 'Play my favorites' and it just works.",
        "source_type": "voice",
        "language": "en",
        "timestamp": "2026-01-10T17:00:00Z",
        "vehicle_model": "ID.4",
        "market": "UK"
    },
    {
        "id": "FB-2026-009",
        "text": "Sprachassistent kann keine Telefonnummern vorlesen. Muss immer aufs Display schauen.",
        "source_type": "voice",
        "language": "de",
        "timestamp": "2026-01-11T08:00:00Z",
        "vehicle_model": "Passat",
        "market": "DE"
    },
    {
        "id": "FB-2026-010",
        "text": "Asystent głosowy nie rozumie polskiego. Muszę mówić po angielsku.",
        "source_type": "voice",
        "language": "pl",
        "timestamp": "2026-01-11T09:00:00Z",
        "vehicle_model": "Golf 8",
        "market": "PL"
    },
    {
        "id": "FB-2026-011",
        "text": "Sprachassistent öffnet falsche App. Sage 'Öffne Spotify' aber er öffnet die Telefon-App.",
        "source_type": "voice",
        "language": "de",
        "timestamp": "2026-01-11T10:30:00Z",
        "vehicle_model": "ID.4",
        "market": "DE"
    },
    {
        "id": "FB-2026-012",
        "text": "Super, dass man jetzt SMS per Sprachassistent diktieren kann. Funktioniert einwandfrei!",
        "source_type": "voice",
        "language": "de",
        "timestamp": "2026-01-11T11:00:00Z",
        "vehicle_model": "ID.5",
        "market": "DE"
    },
    
    # ============ NAVIGATION (8 Einträge) ============
    {
        "id": "FB-2026-020",
        "text": "Navigation zeigt falsche Ankunftszeit. Sagt 30 Minuten aber Google Maps sagt 45 Minuten. Stimmt nie.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T07:00:00Z",
        "vehicle_model": "Passat",
        "market": "DE"
    },
    {
        "id": "FB-2026-021",
        "text": "Kartenmaterial ist veraltet. Neue Straße in meiner Nähe fehlt seit 2 Jahren.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T08:30:00Z",
        "vehicle_model": "ID.5",
        "market": "DE"
    },
    {
        "id": "FB-2026-022",
        "text": "Navigation crashes when entering addresses with special characters like umlauts.",
        "source_type": "error",
        "language": "en",
        "timestamp": "2026-01-10T09:15:00Z",
        "vehicle_model": "ID.4",
        "market": "UK"
    },
    {
        "id": "FB-2026-023",
        "text": "Ladestationen werden in der Navigation nicht korrekt angezeigt. Viele sind falsch markiert.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T10:00:00Z",
        "vehicle_model": "ID.4",
        "market": "DE"
    },
    {
        "id": "FB-2026-024",
        "text": "Die automatische Ladeplanung ist fantastisch! Spart mir viel Zeit auf langen Strecken.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T11:30:00Z",
        "vehicle_model": "ID.5",
        "market": "CH"
    },
    {
        "id": "FB-2026-025",
        "text": "Navigation route takes me through narrow streets when there's a main road available.",
        "source_type": "touch",
        "language": "en",
        "timestamp": "2026-01-10T12:00:00Z",
        "vehicle_model": "Tiguan",
        "market": "UK"
    },
    {
        "id": "FB-2026-026",
        "text": "POI-Suche ist unpraktisch. Tankstellen werden nicht nach Preis sortiert.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T13:00:00Z",
        "vehicle_model": "Golf 8",
        "market": "DE"
    },
    {
        "id": "FB-2026-027",
        "text": "Verkehrsinfo in Echtzeit funktioniert super. Staus werden rechtzeitig umfahren.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T14:00:00Z",
        "vehicle_model": "Passat",
        "market": "AT"
    },
    
    # ============ INFOTAINMENT (10 Einträge) ============
    {
        "id": "FB-2026-030",
        "text": "Bluetooth Verbindung zum iPhone bricht ständig ab. Musik stoppt plötzlich während der Fahrt.",
        "source_type": "error",
        "language": "de",
        "timestamp": "2026-01-10T06:45:00Z",
        "vehicle_model": "Golf 8",
        "market": "DE"
    },
    {
        "id": "FB-2026-031",
        "text": "Radio DAB+ hat schlechten Empfang. UKW funktioniert aber digital nicht.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T07:30:00Z",
        "vehicle_model": "Passat",
        "market": "DE"
    },
    {
        "id": "FB-2026-032",
        "text": "Display reagiert manchmal nicht auf Touch. Muss mehrmals tippen.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T10:45:00Z",
        "vehicle_model": "ID.4",
        "market": "CH"
    },
    {
        "id": "FB-2026-033",
        "text": "CarPlay disconnects randomly. Very annoying during longer trips.",
        "source_type": "error",
        "language": "en",
        "timestamp": "2026-01-10T11:00:00Z",
        "vehicle_model": "ID.5",
        "market": "UK"
    },
    {
        "id": "FB-2026-034",
        "text": "Streaming-Apps wie Spotify laufen flüssig. Keine Beschwerden!",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T12:30:00Z",
        "vehicle_model": "ID.4",
        "market": "DE"
    },
    {
        "id": "FB-2026-035",
        "text": "Android Auto startet nicht automatisch. Muss jedes Mal manuell verbinden.",
        "source_type": "error",
        "language": "de",
        "timestamp": "2026-01-10T13:45:00Z",
        "vehicle_model": "Golf 8",
        "market": "AT"
    },
    {
        "id": "FB-2026-036",
        "text": "Lautstärkeregler am Lenkrad funktioniert nicht mehr nach Update.",
        "source_type": "error",
        "language": "de",
        "timestamp": "2026-01-10T14:30:00Z",
        "vehicle_model": "Tiguan",
        "market": "DE"
    },
    {
        "id": "FB-2026-037",
        "text": "Die neue Podcast-Integration ist super. Endlich native Unterstützung!",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T15:15:00Z",
        "vehicle_model": "ID.5",
        "market": "DE"
    },
    {
        "id": "FB-2026-038",
        "text": "Display brightness is too low in direct sunlight. Can barely see the map.",
        "source_type": "touch",
        "language": "en",
        "timestamp": "2026-01-10T16:00:00Z",
        "vehicle_model": "ID.4",
        "market": "UK"
    },
    {
        "id": "FB-2026-039",
        "text": "Bildschirm friert ein beim Wechsel zwischen Apps. Neustart hilft.",
        "source_type": "error",
        "language": "de",
        "timestamp": "2026-01-10T17:30:00Z",
        "vehicle_model": "Passat",
        "market": "DE"
    },
    
    # ============ KLIMAANLAGE (5 Einträge) ============
    {
        "id": "FB-2026-040",
        "text": "Klimaautomatik kühlt zu stark. Auch auf 22 Grad eingestellt ist es eiskalt.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T12:00:00Z",
        "vehicle_model": "ID.4",
        "market": "DE"
    },
    {
        "id": "FB-2026-041",
        "text": "Sitzheizung über Touch bedienen ist umständlich. Zu viele Klicks nötig.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-10T13:30:00Z",
        "vehicle_model": "ID.5",
        "market": "DE"
    },
    {
        "id": "FB-2026-042",
        "text": "Vorklimatisierung über App funktioniert zuverlässig. Auto ist immer warm wenn ich einsteige.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-11T07:00:00Z",
        "vehicle_model": "ID.4",
        "market": "AT"
    },
    {
        "id": "FB-2026-043",
        "text": "Climate control buttons are too small. Hard to press while driving.",
        "source_type": "touch",
        "language": "en",
        "timestamp": "2026-01-11T08:30:00Z",
        "vehicle_model": "Golf 8",
        "market": "UK"
    },
    {
        "id": "FB-2026-044",
        "text": "Lüftung macht komische Geräusche auf Stufe 3 und höher.",
        "source_type": "error",
        "language": "de",
        "timestamp": "2026-01-11T09:30:00Z",
        "vehicle_model": "Tiguan",
        "market": "DE"
    },
    
    # ============ OTA UPDATES / SOFTWARE (5 Einträge) ============
    {
        "id": "FB-2026-050",
        "text": "OTA Update hat 3 Stunden gedauert. Viel zu lang, Auto war nicht nutzbar.",
        "source_type": "error",
        "language": "de",
        "timestamp": "2026-01-11T02:00:00Z",
        "vehicle_model": "ID.4",
        "market": "DE"
    },
    {
        "id": "FB-2026-051",
        "text": "Nach dem letzten Update spinnt der Spurhalteassistent. Lenkt zu aggressiv gegen.",
        "source_type": "error",
        "language": "de",
        "timestamp": "2026-01-11T08:00:00Z",
        "vehicle_model": "ID.5",
        "market": "AT"
    },
    {
        "id": "FB-2026-052",
        "text": "Software version 3.2 fixed the battery estimation bug. Finally accurate range display!",
        "source_type": "touch",
        "language": "en",
        "timestamp": "2026-01-11T09:30:00Z",
        "vehicle_model": "ID.4",
        "market": "UK"
    },
    {
        "id": "FB-2026-053",
        "text": "Update über Nacht installiert - perfekt! Morgens war alles fertig.",
        "source_type": "touch",
        "language": "de",
        "timestamp": "2026-01-11T10:00:00Z",
        "vehicle_model": "ID.5",
        "market": "DE"
    },
    {
        "id": "FB-2026-054",
        "text": "Aktualizacja oprogramowania trwała zbyt długo. Auto było niedostępne przez 4 godziny.",
        "source_type": "error",
        "language": "pl",
        "timestamp": "2026-01-11T11:00:00Z",
        "vehicle_model": "Golf 8",
        "market": "PL"
    },
]


async def seed_demo_data():
    """Demo-Daten in VectorStore laden."""
    print("🚀 Lade Demo-Daten...")
    
    vs = VectorStoreService()
    
    # Prüfen ob schon Daten vorhanden
    count = await vs.count()
    if count > 0:
        print(f"⚠️  VectorStore enthält bereits {count} Dokumente.")
        print("   Überspringe Seeding.")
        return
    
    # Daten laden
    await vs.add_documents(DEMO_FEEDBACKS)
    
    new_count = await vs.count()
    print(f"✅ {new_count} Demo-Feedbacks geladen!")
    print("\nBeispiel-Fragen zum Testen:")
    print("  - Welche Probleme gibt es mit dem Sprachassistenten?")
    print("  - Was sagen Kunden zur Navigation?")
    print("  - Gibt es positives Feedback?")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
