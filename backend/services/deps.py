"""
Globale VectorStore Instanz (Singleton)

Stellt sicher, dass alle Komponenten dieselbe VectorStore-Instanz nutzen.
"""

from services.vectorstore import VectorStoreService

# Globale Instanz
_vectorstore: VectorStoreService | None = None


def get_vectorstore() -> VectorStoreService:
    """Gibt die globale VectorStore-Instanz zurück."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = VectorStoreService()
    return _vectorstore
