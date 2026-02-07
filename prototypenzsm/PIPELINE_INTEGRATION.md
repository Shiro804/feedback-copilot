# Pipeline Integration Guide

## Quick Setup (Beide Projekte lokal)

### 1. Feedback-Copilot starten

```bash
# Terminal 1: Backend (Port 8000)
cd feedback-copilot/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend (Port 3000)
cd feedback-copilot/frontend
npm install && npm run dev
```

### 2. ASR-Stack starten

```bash
# Terminal 3: Streamlit (Port 8501)
cd asr-stack
pip install -r requirements.txt
streamlit run app.py
```

---

## API-Endpoint für Daten-Ingest

### POST `/api/ingest/stream`

**URL:** `http://localhost:8000/api/ingest/stream`

**Akzeptierte Formate:**

1. **JSONL** (empfohlen):
```
{"text":"Navigation geht nicht","label":"NAVIGATION","vehicle_model":"ID.4","market":"DE"}
{"text":"Klimaanlage zu kalt","label":"CLIMATE","vehicle_model":"Golf 8","market":"DE"}
```

2. **JSON-Array:**
```json
[
  {"text":"Navigation geht nicht","label":"NAVIGATION"},
  {"text":"Klimaanlage zu kalt","label":"CLIMATE"}
]
```

---

## Beispiel: Python-Integration

```python
import requests

def send_to_feedback_copilot(feedbacks: list):
    """Sendet Feedbacks an den Feedback-Copilot."""
    response = requests.post(
        "http://localhost:8000/api/ingest/stream",
        json=feedbacks,
        headers={"Content-Type": "application/json"}
    )
    return response.json()

# Beispiel-Aufruf
result = send_to_feedback_copilot([
    {
        "text": "Der Sprachassistent versteht mich nicht",
        "label": "INFOTAINMENT",
        "vehicle_model": "ID.4",
        "market": "DE",
        "source_type": "voice"
    }
])
print(result)  # {"success": true, "processed": 1, ...}
```

---

## Feldmapping (ASR → Feedback-Copilot)

| ASR-Stack Feld | Feedback-Copilot Feld | Automatisches Mapping |
|----------------|----------------------|----------------------|
| `transcript` | `text` | ✅ |
| `emotion` | `style` | anger→complaint, joy→praise |
| `intent` | `label` | 10 Kategorien |
| `sentiment` | `sentiment` | positive/negative/neutral |
| `is_feedback` | - | Nur true senden |
| - | `source_type` | Default: "voice" |
| - | `vehicle_model` | Muss mitgesendet werden |
| - | `market` | Muss mitgesendet werden |

---

## Test mit cURL

```bash
# Einzelnes Feedback
curl -X POST http://localhost:8000/api/ingest/stream \
  -H "Content-Type: application/json" \
  -d '{"text":"Test Feedback","label":"NAVIGATION","vehicle_model":"ID.4","market":"DE"}'

# Prüfen ob angekommen
curl http://localhost:8000/api/feedbacks/stats
```

---

## Ports-Übersicht

| Service | Port | URL |
|---------|------|-----|
| Feedback-Copilot Backend | 8000 | http://localhost:8000 |
| Feedback-Copilot Frontend | 3000 | http://localhost:3000 |
| ASR-Stack (Streamlit) | 8501 | http://localhost:8501 |
