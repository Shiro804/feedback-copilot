"""VectorStore Service - ChromaDB mit Hybrid Search und Cross-Encoder Reranking."""

from typing import List, Optional, Dict
import chromadb
from chromadb.config import Settings
import os
import re

# BM25 für Keyword-basierte Suche
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("rank_bm25 nicht installiert - nur Vector-Suche verfügbar")

# Cross-Encoder für Reranking
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    print("sentence-transformers nicht installiert - kein Cross-Encoder Reranking")

# NLTK Stemming
try:
    import nltk
    from nltk.stem import PorterStemmer
    from nltk.tokenize import word_tokenize
    # Download required data (silent)
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)
    NLTK_AVAILABLE = True
    stemmer = PorterStemmer()
except ImportError:
    NLTK_AVAILABLE = False
    stemmer = None
    print("nltk nicht installiert - einfache Tokenisierung")


# Englische Stopwords (häufigste, für Performance kompakt gehalten)
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "was", "are", "were", "been", "be", "have",
    "has", "had", "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "must", "shall", "can", "this", "that", "these", "those", "i", "you",
    "he", "she", "it", "we", "they", "what", "which", "who", "when", "where",
    "why", "how", "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "no", "not", "only", "same", "so", "than", "too", "very",
    "just", "also", "now", "here", "there", "then", "if", "my", "your", "his",
    "her", "its", "our", "their", "me", "him", "us", "them", "am", "about"
}


def tokenize(text: str) -> List[str]:
    """Tokenisierung für BM25 mit optionalem NLTK Stemming."""
    text = text.lower()
    
    if NLTK_AVAILABLE:
        # NLTK Tokenisierung + Stemming
        try:
            tokens = word_tokenize(text)
            tokens = [stemmer.stem(t) for t in tokens if t.isalnum()]
        except:
            # Fallback bei NLTK-Fehler
            tokens = re.findall(r'\b[a-z0-9]+\b', text)
    else:
        # Fallback: Regex-basiert
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
    
    # Stopwords entfernen und Mindestlänge prüfen
    return [t for t in tokens if t not in STOPWORDS and len(t) >= 2]


class VectorStoreService:
    """VectorStore mit ChromaDB + Hybrid Retrieval + Cross-Encoder Reranking."""
    
    def __init__(self):
        # Persistentes Verzeichnis für ChromaDB
        persist_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
        
        # ChromaDB mit Persistenz initialisieren
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Collection für Feedback (nutzt default embedding function)
        self.collection = self.client.get_or_create_collection(
            name="feedback"
        )
        
        # BM25-Index Cache
        self._bm25_index = None
        self._bm25_docs = []
        self._bm25_ids = []
        self._bm25_doc_count = 0
        
        # Cross-Encoder (lazy loading)
        self._cross_encoder = None
        self._cross_encoder_loaded = False
    
    def _get_cross_encoder(self):
        """Cross-Encoder lazy laden."""
        if not CROSS_ENCODER_AVAILABLE:
            return None
        
        if not self._cross_encoder_loaded:
            try:
                # Kompaktes aber effektives Modell
                self._cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                print("Cross-Encoder geladen (ms-marco-MiniLM-L-6-v2)")
            except Exception as e:
                print(f"Cross-Encoder konnte nicht geladen werden: {e}")
                self._cross_encoder = None
            self._cross_encoder_loaded = True
        
        return self._cross_encoder
    
    async def add_documents(self, documents: List[dict]) -> int:
        """Dokumente zum VectorStore hinzufügen - unterstützt neues und altes Schema."""
        if not documents:
            return 0
        
        ids = [doc.get("id", str(i)) for i, doc in enumerate(documents)]
        texts = [doc.get("text", "") for doc in documents]
        metadatas = []
        
        for doc in documents:
            meta = {}
            # Neues Schema (10K Datensatz)
            if doc.get("label"):
                meta["label"] = doc["label"]
            if doc.get("style"):
                meta["style"] = doc["style"]
            if doc.get("length_bucket"):
                meta["length_bucket"] = doc["length_bucket"]
            if doc.get("confidence") is not None:
                meta["confidence"] = float(doc["confidence"])
            
            # Legacy Schema (Kompatibilität)
            if doc.get("source_type"):
                meta["source_type"] = doc["source_type"]
            if doc.get("language"):
                meta["language"] = doc["language"]
            if doc.get("timestamp"):
                meta["timestamp"] = doc["timestamp"]
            if doc.get("vehicle_model"):
                meta["vehicle_model"] = doc["vehicle_model"]
            if doc.get("market"):
                meta["market"] = doc["market"]
            
            metadatas.append(meta)
        
        # In ChromaDB speichern
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        
        # BM25-Cache invalidieren
        self._bm25_index = None
        
        return len(documents)
    
    def _should_rebuild_bm25(self) -> bool:
        """Prüft ob BM25-Index neu gebaut werden muss."""
        current_count = self.collection.count()
        return self._bm25_index is None or current_count != self._bm25_doc_count
    
    def _build_bm25_index(self):
        """
        BM25-Index für Keyword-Suche aufbauen.
        
        Mit NLTK Stemming für besseren Recall.
        """
        if not BM25_AVAILABLE:
            return
        
        if not self._should_rebuild_bm25():
            return
        
        all_docs = self.collection.get(include=["documents"])
        
        if not all_docs["ids"]:
            return
        
        self._bm25_ids = all_docs["ids"]
        self._bm25_docs = all_docs["documents"]
        self._bm25_doc_count = len(self._bm25_ids)
        
        # Tokenisierung mit Stemming
        tokenized = [tokenize(doc) for doc in self._bm25_docs]
        self._bm25_index = BM25Okapi(tokenized)
    
    def _cross_encoder_rerank(self, query: str, candidates: List[Dict], top_k: int) -> List[Dict]:
        """Cross-Encoder Reranking für höhere Retrieval-Qualität."""
        cross_encoder = self._get_cross_encoder()
        
        if not cross_encoder or len(candidates) == 0:
            return candidates[:top_k]
        
        # Query-Document Paare erstellen
        pairs = [(query, c["text"]) for c in candidates]
        
        # Cross-Encoder Scores berechnen
        try:
            scores = cross_encoder.predict(pairs)
            
            # Scores zu Kandidaten hinzufügen
            for i, candidate in enumerate(candidates):
                candidate["cross_encoder_score"] = float(scores[i])
            
            # Nach Cross-Encoder Score sortieren
            reranked = sorted(candidates, key=lambda x: x.get("cross_encoder_score", 0), reverse=True)
            
            return reranked[:top_k]
        
        except Exception as e:
            print(f"Cross-Encoder Reranking fehlgeschlagen: {e}")
            return candidates[:top_k]
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        use_hybrid: bool = True,
        use_reranking: bool = True,  # NEU: Cross-Encoder Reranking
        filters: Optional[dict] = None
    ) -> List[Dict]:
        """Hybrid Search mit BM25 + Vector und optionalem Cross-Encoder Reranking."""
        # Where-Filter aufbauen
        where_filter = None
        if filters:
            where_filter = {k: v for k, v in filters.items() if v}
        
        # === VECTOR SEARCH ===
        try:
            vector_results = self.collection.query(
                query_texts=[query],
                n_results=top_k * 3,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            return []
        
        vector_rankings = {}
        if vector_results and vector_results.get("ids") and vector_results["ids"][0]:
            for rank, doc_id in enumerate(vector_results["ids"][0]):
                vector_rankings[doc_id] = {
                    "rank": rank + 1,
                    "text": vector_results["documents"][0][rank],
                    "metadata": vector_results["metadatas"][0][rank] if vector_results.get("metadatas") else {},
                    "distance": vector_results["distances"][0][rank] if vector_results.get("distances") else 0
                }
        
        # === BM25 SEARCH ===
        bm25_rankings = {}
        if use_hybrid and BM25_AVAILABLE:
            self._build_bm25_index()
            
            if self._bm25_index:
                tokenized_query = tokenize(query)
                
                if tokenized_query:
                    bm25_scores = self._bm25_index.get_scores(tokenized_query)
                    scored_docs = sorted(zip(self._bm25_ids, bm25_scores), key=lambda x: x[1], reverse=True)
                    
                    for rank, (doc_id, score) in enumerate(scored_docs[:top_k * 3]):
                        if score > 0:
                            bm25_rankings[doc_id] = {"rank": rank + 1, "score": score}
        
        # === RRF FUSION ===
        k = 60
        rrf_scores = {}
        all_doc_ids = set(vector_rankings.keys()) | set(bm25_rankings.keys())
        
        for doc_id in all_doc_ids:
            rrf_score = 0
            boost = 1.0
            
            if doc_id in vector_rankings:
                rrf_score += 1 / (k + vector_rankings[doc_id]["rank"])
                distance = vector_rankings[doc_id]["distance"]
                if distance < 0.3:
                    boost = 1.2
                elif distance < 0.5:
                    boost = 1.1
            
            if doc_id in bm25_rankings:
                rrf_score += 1 / (k + bm25_rankings[doc_id]["rank"])
                if doc_id in vector_rankings:
                    boost *= 1.1
            
            rrf_scores[doc_id] = rrf_score * boost
        
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # Kandidaten für Reranking vorbereiten
        candidates = []
        for doc_id in sorted_ids[:top_k * 2]:  # Mehr für Reranking
            info = vector_rankings.get(doc_id)
            if info:
                method = "hybrid" if doc_id in bm25_rankings else "vector"
                candidates.append({
                    "id": doc_id,
                    "text": info["text"],
                    "score": rrf_scores[doc_id],
                    "metadata": info["metadata"],
                    "retrieval_method": method,
                    "vector_distance": info["distance"]
                })
            elif doc_id in bm25_rankings:
                try:
                    doc_data = self.collection.get(ids=[doc_id], include=["documents", "metadatas"])
                    candidates.append({
                        "id": doc_id,
                        "text": doc_data["documents"][0] if doc_data["documents"] else "",
                        "score": rrf_scores[doc_id],
                        "metadata": doc_data["metadatas"][0] if doc_data.get("metadatas") else {},
                        "retrieval_method": "bm25",
                        "vector_distance": None
                    })
                except:
                    pass
        
        # === CROSS-ENCODER RERANKING ===
        if use_reranking and CROSS_ENCODER_AVAILABLE:
            candidates = self._cross_encoder_rerank(query, candidates, top_k)
        else:
            candidates = candidates[:top_k]
        
        return candidates
    
    async def count(self) -> int:
        """Anzahl der Dokumente im VectorStore."""
        return self.collection.count()
    
    async def delete(self, ids: List[str]) -> int:
        """Dokumente löschen."""
        self.collection.delete(ids=ids)
        self._bm25_index = None
        return len(ids)
