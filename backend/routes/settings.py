"""
Settings Route - Globale Konfiguration für RAG-Pipeline

Endpoints:
- GET /settings - Aktuelle Einstellungen laden
- PUT /settings - Einstellungen speichern

Einstellungen werden in settings.json persistiert.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
from typing import Optional

router = APIRouter(prefix="/api/settings", tags=["Settings"])

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"

# Default-Einstellungen
DEFAULT_SETTINGS = {
    "temperature": 0.3,
    "citation_required": True,
    "unanswerable_guard": True,
    "confliction_detection": True
}


class SettingsModel(BaseModel):
    temperature: float = 0.3
    citation_required: bool = True
    unanswerable_guard: bool = True
    confliction_detection: bool = True


def load_settings() -> dict:
    """Einstellungen aus Datei laden."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except Exception:
            return DEFAULT_SETTINGS
    return DEFAULT_SETTINGS


def save_settings(settings: dict) -> None:
    """Einstellungen in Datei speichern."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


# Globale Settings (für Import in anderen Modulen)
_settings_cache: Optional[dict] = None


def get_settings() -> dict:
    """Globale Settings abrufen (mit Cache)."""
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = load_settings()
    return _settings_cache


def refresh_settings() -> dict:
    """Settings neu laden (nach Änderung)."""
    global _settings_cache
    _settings_cache = load_settings()
    return _settings_cache


@router.get("/")
async def get_settings_endpoint():
    """Aktuelle Einstellungen abrufen."""
    return get_settings()


@router.put("/")
async def update_settings(settings: SettingsModel):
    """Einstellungen speichern."""
    settings_dict = settings.model_dump()
    save_settings(settings_dict)
    refresh_settings()  # Cache aktualisieren
    return {
        "success": True,
        "settings": settings_dict
    }


@router.post("/reset")
async def reset_settings():
    """Einstellungen zurücksetzen."""
    save_settings(DEFAULT_SETTINGS)
    refresh_settings()
    return {
        "success": True,
        "settings": DEFAULT_SETTINGS
    }
