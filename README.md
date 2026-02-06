# Feedback-Copilot

RAG-basierte Analyse von In-Car Kundenfeedback für Volkswagen.

**Masterarbeit:** Oguz Selim Semir  
**Literatur-Basis:** 86 Papers (IEEE, MDPI, ScienceDirect)

---

## 🎯 Forschungsfrage

> *Wie gestaltet man eine RAG-Pipeline, die auf erhobenen und anonymisierten In-Car-Feedbackdaten verlässlich, nachvollziehbar und latenzarm Antworten und Artefakte liefert?*

---

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: Next.js 14 + Mantine UI                              │
│  Dashboard │ Chat │ Ingest │ Analytics │ Export                 │
├─────────────────────────────────────────────────────────────────┤
│  BACKEND: FastAPI (Python)                                       │
│  /api/chat │ /api/ingest │ /api/search │ /api/analytics         │
├─────────────────────────────────────────────────────────────────┤
│  RAG-PIPELINE (LangChain)                                        │
│  Hybrid Retrieval (BM25+Vector) │ Guardrails │ Zitationspflicht │
├─────────────────────────────────────────────────────────────────┤
│  DATEN                                                           │
│  ChromaDB (Vector) │ Multilingual Embeddings │ PII-Filter       │
├─────────────────────────────────────────────────────────────────┤
│  LLM: OpenAI GPT-4o                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 Literatur-Referenzen

| Komponente | Paper |
|------------|-------|
| RAG-Framework | Yang et al. (2025): RAGVA |
| Hybrid Retrieval | Praneeth et al. (2025): Advanced RAG |
| Guardrails | Wu & Wu (2025): Confliction Detection |
| Embeddings | Lin et al. (2024): Domain Adaption |
| PII-Filter | **Forschungslücke** (eigener Beitrag) |

---

## 🚀 Schnellstart

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# .env erstellen
cp .env.example .env
# OPENAI_API_KEY eintragen

# Starten
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Öffne http://localhost:3000

---

## 📁 Projektstruktur

```
feedback-copilot/
├── backend/
│   ├── main.py              # FastAPI App
│   ├── routes/
│   │   ├── chat.py          # RAG Chat Endpoint
│   │   ├── ingest.py        # Feedback-Import
│   │   ├── search.py        # Hybrid Search
│   │   └── analytics.py     # Trend-Analyse
│   ├── services/
│   │   ├── rag.py           # LangChain + OpenAI
│   │   ├── pii.py           # Anonymisierung
│   │   └── vectorstore.py   # ChromaDB
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Dashboard
│   │   ├── chat/            # RAG Chat Interface
│   │   ├── ingest/          # Feedback-Upload
│   │   ├── analytics/       # Charts
│   │   ├── export/          # Ticket-Generator
│   │   └── settings/        # Konfiguration
│   └── components/
│       └── MainContainer.tsx
│
└── README.md
```

---

## ✅ Features (aus Onepager)

- [x] RAG-basierte Q&A mit Quellenangabe
- [x] Hybrid Retrieval (BM25 + Embeddings)
- [x] PII-Anonymisierung (NER + Regex)
- [x] Mehrsprachig (DE/EN/PL)
- [x] Trend-Charts und Top-Aspekte
- [x] Ticket-Export (JSON/CSV/MD)
- [x] Guardrails: Zitationspflicht, Unanswerable

---

## 📊 Evaluation (geplant)

| Metrik | Ziel |
|--------|------|
| Recall@5 | > 0.8 |
| Citation Coverage | > 90% |
| Latenz | < 3s |

---

*Erstellt: Januar 2026*
