"""
Query Supervisor & Script Router Agent.
Analyzes input query, detects script and language, manages state transitions, and routes tasks.
"""

import unicodedata
from typing import Any, Dict
from indicsql.core.state import IndicSQLState


def detect_indic_script(text: str) -> str:
    """
    Detects the Unicode script of the input text based on character Unicode blocks.
    Supports Devanagari, Bengali, Tamil, Telugu, and Latin (Hinglish/English).
    """
    for ch in text:
        name = unicodedata.name(ch, "")
        if "DEVANAGARI" in name:
            return "Devanagari"
        if "BENGALI" in name:
            return "Bengali"
        if "TAMIL" in name:
            return "Tamil"
        if "TELUGU" in name:
            return "Telugu"
    return "Latin"


def identify_language_code(text: str, script: str) -> str:
    """
    Identifies the language code ('hi', 'bn', 'ta', 'te', 'mr', 'hi-en', 'en').
    """
    if script == "Tamil":
        return "ta"
    if script == "Telugu":
        return "te"
    if script == "Bengali":
        return "bn"
    if script == "Devanagari":
        # Heuristic check for Marathi specific characters (like ळ) or words
        if "ळ" in text or "आहे" in text or "किती" in text or "शेतकऱ्यांना" in text:
            return "mr"
        return "hi"
    
    # For Latin script: Distinguish Hinglish vs English
    hinglish_markers = {"kitne", "kisko", "pichle", "saal", "me", "mein", "ka", "ki", "ke", "hai", "kya", "yojana"}
    words = set(text.lower().split())
    if words.intersection(hinglish_markers):
        return "hi-en"
    return "en"


def supervisor_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Supervisor Agent node: Ingests raw query, identifies language & script,
    initializes audit trace and canonical query.
    """
    raw_query = state.get("raw_query", "").strip()
    script = detect_indic_script(raw_query)
    lang = identify_language_code(raw_query, script)

    audit_entry = {
        "step": 1,
        "agent": "SupervisorRouter",
        "action": "normalize_and_detect",
        "detected_script": script,
        "detected_language": lang,
    }

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "detected_script": script,
        "detected_lang": lang,
        "canonical_query": raw_query,
        "reflection_attempts": state.get("reflection_attempts", 0),
        "audit_trace": current_trace,
    }
