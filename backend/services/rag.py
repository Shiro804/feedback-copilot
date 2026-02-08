"""RAG Service - LangChain + OpenAI Integration für Feedback-Analyse."""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# SAIA API Client (OpenAI-kompatible Uni-API)
# Dokumentation: https://docs.hpc.gwdg.de/services/saia/
api_key = os.getenv("API_KEY")
base_url = "https://chat-ai.academiccloud.de/v1"
client = None
if api_key:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

from services.deps import get_vectorstore

# Settings dynamisch laden
def get_rag_settings():
    """RAG-Settings laden (mit Fallback)."""
    try:
        from routes.settings import get_settings
        return get_settings()
    except:
        return {"temperature": 0.3, "citation_required": True, "unanswerable_guard": True}


def strip_metadata_prefix(text: str) -> str:
    """
    Entfernt Metadaten-Prefix aus dem Text für cleane Anzeige.
    Input:  "[ID.4] [DE] [voice] [NAVIGATION] Die Navigation funktioniert nicht"
    Output: "Die Navigation funktioniert nicht"
    """
    import re
    # Entferne alle [xxx] Tags am Anfang des Textes
    return re.sub(r'^(\[[^\]]*\]\s*)+', '', text).strip()


class RAGService:
    """RAG-Pipeline für Feedback-Analyse."""
    
    def __init__(self):
        self.vectorstore = get_vectorstore()
        self.model = "openai-gpt-oss-120b"  # SAIA GPT Model
        self.max_context_tokens = 4000
    
    async def query(
        self,
        question: str,
        language: str = "de",
        max_sources: int = 10  # Erhöht für besseren Kontext bei 10 Kategorien
    ) -> dict:
        """RAG-Anfrage mit Quellenangabe."""
        
        # Settings dynamisch laden
        settings = get_rag_settings()
        
        # 1. Retrieval
        sources = await self.vectorstore.search(
            query=question,
            top_k=max_sources,
            use_hybrid=True
        )
        
        # 2. Check: Gibt es relevante Quellen?
        if not sources:
            if settings.get("unanswerable_guard", True):
                return {
                    "answer": self._get_unanswerable_message(language),
                    "sources": [],
                    "confidence": 0.0,
                    "answerable": False
                }
        
        # 2.5 Check: OpenAI Client verfügbar?
        if client is None:
            return {
                "answer": "[DEMO-MODUS] OpenAI API Key nicht konfiguriert. Bitte in .env eintragen.",
                "sources": [{"id": s.get("id", ""), "text": s.get("text", "")[:100], "score": s.get("score", 0), "metadata": {}} for s in sources[:3]],
                "confidence": 0.5,
                "answerable": True
            }
        
        # 3. Context aufbauen
        context = self._build_context(sources)
        
        # 4. LLM-Generierung mit Zitationspflicht (dynamische Temperature)
        system_prompt = self._get_system_prompt(language, settings)
        
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Kontext:\n{context}\n\nFrage: {question}"}
            ],
            temperature=settings.get("temperature", 0.3),
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        
        # 5. Relevanz-Filter: Nur Quellen mit Score über Schwellenwert
        MIN_RELEVANCE_SCORE = 0.015  # Schwellenwert für Relevanz
        relevant_sources = [s for s in sources if s.get("score", 0) >= MIN_RELEVANCE_SCORE]
        
        # 6. Wenn LLM sagt "nicht verfügbar", Quellen ausblenden
        no_answer_indicators = [
            "liegt nicht vor", "nicht vor", "not available", 
            "keine relevanten", "no relevant", "cannot answer"
        ]
        if any(indicator in answer.lower() for indicator in no_answer_indicators):
            relevant_sources = []
        
        # 7. Confidence berechnen
        avg_score = sum(s.get("score", 0) for s in relevant_sources) / len(relevant_sources) if relevant_sources else 0
        
        return {
            "answer": answer,
            "sources": [
                {
                    "id": s.get("id", ""),
                    "text": strip_metadata_prefix(s.get("text", ""))[:200],
                    "score": s.get("score", 0),
                    "metadata": s.get("metadata", {})
                }
                for s in relevant_sources
            ],
            "confidence": avg_score,
            "answerable": len(relevant_sources) > 0
        }
    
    def _build_context(self, sources: List[dict]) -> str:
        """Kontext aus Quellen aufbauen mit IDs für Zitation."""
        context_parts = []
        for i, source in enumerate(sources):
            source_id = source.get("id", f"Q{i+1}")
            # Text bleibt mit Metadaten für LLM-Kontext (hilfreich für Modell-spezifische Fragen)
            text = source.get("text", "")
            context_parts.append(f"[{source_id}]: {text}")
        return "\n\n".join(context_parts)
    
    def _get_system_prompt(self, language: str, settings: dict = None) -> str:
        """System-Prompt mit konfigurierbarer Zitationspflicht."""
        if settings is None:
            settings = {"citation_required": True}
        
        citation_rule = ""
        if settings.get("citation_required", True):
            citation_rule = "2. Zitiere JEDE Aussage mit [Quellen-ID]\n"
            citation_format = "\n\nFormat: Antworte auf Deutsch, zitiere mit [Q1], [Q2], etc."
        else:
            citation_rule = ""
            citation_format = ""
        
        if language == "de":
            return f"""Du bist ein Feedback-Analyst für Volkswagen Fahrzeuge.

WICHTIGE REGELN:
1. Beantworte NUR basierend auf den gegebenen Quellen
{citation_rule}3. Sage "Diese Information liegt nicht vor" wenn keine Evidenz
4. Fasse Feedback-Trends zusammen wenn gefragt
5. Bleibe sachlich und faktenbasiert{citation_format}"""
        else:
            cite_en = "\n2. CITE every statement with [Source-ID]" if settings.get("citation_required", True) else ""
            format_en = "\n\nFormat: Answer in English, cite with [Q1], [Q2], etc." if settings.get("citation_required", True) else ""
            return f"""You are a feedback analyst for Volkswagen vehicles.

IMPORTANT RULES:
1. Answer ONLY based on the provided sources{cite_en}
3. Say "This information is not available" if no evidence
4. Summarize feedback trends when asked
5. Stay factual and evidence-based{format_en}"""
    
    def _get_unanswerable_message(self, language: str) -> str:
        """Nachricht wenn keine relevanten Quellen gefunden."""
        if language == "de":
            return "Zu dieser Frage liegen keine relevanten Feedback-Daten vor. Bitte formulieren Sie die Frage um oder überprüfen Sie, ob passende Daten importiert wurden."
        return "No relevant feedback data is available for this question. Please rephrase or verify that appropriate data has been imported."
