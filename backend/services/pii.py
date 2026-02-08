"""PII Service - Anonymisierung personenbezogener Daten vor Indizierung."""

import re
import hashlib
from typing import Tuple, List, Dict, Optional

# Try to import spaCy for NER
try:
    import spacy
    _SPACY_AVAILABLE = True
except ImportError:
    _SPACY_AVAILABLE = False
    spacy = None


class PIIService:
    """
    PII-Anonymisierung für Feedback-Texte.
    
    Erkannte PII-Typen:
    - Namen (via spaCy NER - falls verfügbar)
    - Orte (via spaCy NER - falls verfügbar)  
    - E-Mail-Adressen (Regex)
    - Telefonnummern (Regex)
    - Kennzeichen (Regex, DE-Format)
    - VIN-Nummern (Regex, 17-stellig)
    """
    
    def __init__(self, use_ner: bool = True):
        # Regex-Patterns für automotive-spezifische PII
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone_de": r'\b(?:\+49|0049|0)[\s\-]?(?:\d{2,4})[\s\-]?\d{3,8}\b',
            "plate_de": r'\b[A-ZÄÖÜ]{1,3}[\s\-]?[A-Z]{1,2}[\s\-]?\d{1,4}[EH]?\b',
            "vin": r'\b[A-HJ-NPR-Z0-9]{17}\b',
            "date_de": r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b',
        }
        
        # Placeholder für anonymisierte Daten
        self.placeholders = {
            "email": "[EMAIL]",
            "phone_de": "[TELEFON]",
            "plate_de": "[KENNZEICHEN]",
            "vin": "[VIN]",
            "date_de": "[DATUM]",
            "person": "[NAME]",
            "PER": "[NAME]",
            "location": "[ORT]",
            "LOC": "[ORT]",
            "GPE": "[ORT]",
            "ORG": "[FIRMA]",
        }
        
        # spaCy NER-Modell laden (optional)
        self.nlp = None
        self.use_ner = use_ner
        
        if use_ner and _SPACY_AVAILABLE:
            try:
                # Versuche deutsches Modell zu laden
                self.nlp = spacy.load("de_core_news_sm")
                print("spaCy NER aktiviert (de_core_news_sm)")
            except OSError:
                try:
                    # Fallback auf englisches Modell
                    self.nlp = spacy.load("en_core_web_sm")
                    print("spaCy NER aktiviert (en_core_web_sm)")
                except OSError:
                    print("spaCy NER nicht verfügbar - nur Regex-basierte Anonymisierung")
                    self.nlp = None
    
    def _ner_anonymize(self, text: str) -> Tuple[str, List[Dict]]:
        """
        NER-basierte Anonymisierung für Namen und Orte.
        Gibt (anonymisierten_text, erkannte_entities) zurück.
        """
        if not self.nlp:
            return text, []
        
        doc = self.nlp(text)
        detected = []
        anonymized = text
        
        # Entities in umgekehrter Reihenfolge verarbeiten (um Positionsverschiebungen zu vermeiden)
        entities = sorted(doc.ents, key=lambda e: e.start_char, reverse=True)
        
        for ent in entities:
            # Nur PER (Person), LOC (Ort), GPE (Geo-Political Entity), ORG (Organisation)
            if ent.label_ in ["PER", "LOC", "GPE", "ORG"]:
                placeholder = self.placeholders.get(ent.label_, "[REDACTED]")
                
                detected.append({
                    "type": ent.label_,
                    "original_hash": self._hash(ent.text),
                    "position": ent.start_char,
                    "length": len(ent.text),
                    "label": ent.label_
                })
                
                # Ersetze nur diese spezifische Entität
                anonymized = anonymized[:ent.start_char] + placeholder + anonymized[ent.end_char:]
        
        return anonymized, detected
    
    def anonymize(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Text anonymisieren und erkannte PII zurückgeben.
        Nutzt sowohl NER (für Namen/Orte) als auch Regex (für VIN, Email, etc.)
        
        Returns:
            Tuple: (anonymisierter_text, liste_der_erkannten_pii)
        """
        detected_pii = []
        anonymized = text
        
        # 1. Zuerst NER-basierte Anonymisierung (für Namen und Orte)
        if self.use_ner and self.nlp:
            anonymized, ner_detected = self._ner_anonymize(anonymized)
            detected_pii.extend(ner_detected)
        
        # 2. Dann Regex-basierte Anonymisierung (für strukturierte PII)
        for pii_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, anonymized, re.IGNORECASE)
            for match in matches:
                original = match.group()
                placeholder = self.placeholders.get(pii_type, "[REDACTED]")
                
                detected_pii.append({
                    "type": pii_type,
                    "original_hash": self._hash(original),
                    "position": match.start(),
                    "length": len(original)
                })
                
                anonymized = anonymized.replace(original, placeholder)
        
        return anonymized, detected_pii
    
    def anonymize_batch(self, texts: List[str]) -> List[Tuple[str, List[Dict]]]:
        """Mehrere Texte anonymisieren."""
        return [self.anonymize(text) for text in texts]
    
    def _hash(self, value: str) -> str:
        """SHA-256 Hash für pseudonymisierung."""
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    def detect_only(self, text: str) -> List[Dict]:
        """PII erkennen ohne zu anonymisieren (für Preview)."""
        detected = []
        
        # NER-Erkennung
        if self.use_ner and self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["PER", "LOC", "GPE", "ORG"]:
                    detected.append({
                        "type": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "text": ent.text,
                        "source": "ner"
                    })
        
        # Regex-Erkennung
        for pii_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                detected.append({
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(),
                    "source": "regex"
                })
        
        return detected
    
    def get_status(self) -> Dict:
        """Status des PII-Services zurückgeben."""
        return {
            "ner_available": self.nlp is not None,
            "ner_model": self.nlp.meta.get("name") if self.nlp else None,
            "regex_patterns": list(self.patterns.keys()),
            "spacy_installed": _SPACY_AVAILABLE
        }
