"""
Feedback-Copilot Backend
RAG-basierte Analyse von In-Car Kundenfeedback

Literatur-Basis:
- Yang et al. (2025): RAGVA - Engineering RAG-based Virtual Assistants
- Wu & Wu (2025): Confliction Detection in RAG
- Lin et al. (2024): Domain Adaption for Dialog Systems
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.chat import router as chat_router
from routes.ingest import router as ingest_router
from routes.search import router as search_router
from routes.analytics import router as analytics_router
from routes.feedbacks import router as feedbacks_router
from routes.evaluate import router as evaluate_router
from routes.export import router as export_router
from routes.settings import router as settings_router

app = FastAPI(
    title="Feedback-Copilot API",
    description="RAG-basierte Analyse von In-Car Kundenfeedback für VW",
    version="0.1.0"
)

# CORS für Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routen registrieren
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(ingest_router, prefix="/api/ingest", tags=["Ingest"])
app.include_router(search_router, prefix="/api/search", tags=["Search"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(feedbacks_router, prefix="/api/feedbacks", tags=["Feedbacks"])
app.include_router(evaluate_router, prefix="/api/evaluate", tags=["Evaluate"])
app.include_router(export_router, prefix="/api/export", tags=["Export"])
app.include_router(settings_router)


@app.get("/")
async def root():
    return {"message": "Feedback-Copilot API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/debug/vectorstore")
async def debug_vectorstore():
    """Debug: VectorStore-Status prüfen."""
    from services.deps import get_vectorstore
    vs = get_vectorstore()
    count = await vs.count()
    # Teste eine Suche
    results = await vs.search("Sprachassistent", top_k=3)
    return {
        "count": count,
        "test_search_results": len(results),
        "sample_results": [{"id": r["id"], "score": r["score"]} for r in results]
    }


# Startup Event: Demo-Daten laden
@app.on_event("startup")
async def startup_event():
    """Lade Demo-Daten beim Start."""
    from seed_demo import DEMO_FEEDBACKS
    from services.deps import get_vectorstore
    
    vs = get_vectorstore()
    count = await vs.count()
    
    if count == 0:
        print("🚀 Lade Demo-Daten beim Start...")
        await vs.add_documents(DEMO_FEEDBACKS)
        print(f"✅ {len(DEMO_FEEDBACKS)} Demo-Feedbacks geladen!")
    else:
        print(f"📊 VectorStore enthält bereits {count} Dokumente.")
