"""
Phonetic and Transliteration Normalization Module.
Bridges Latin transliteration (Hinglish/Tanglish) and regional Indic Unicode variations
to canonical vocabulary terms.
"""

import re
from typing import Dict


# Common Latin-to-canonical mappings for Indian administrative terms
TRANSLITERATION_MAP: Dict[str, str] = {
    "kisan": "farmer",
    "kisano": "farmer",
    "shala": "school",
    "vidyarthi": "student",
    "rojgar": "employment",
    "mandays": "mandays",
    "yojana": "scheme",
    "saksharta": "literacy",
    "pichle": "previous",
    "saal": "year",
    "rajya": "state",
    "jila": "district",
    "jile": "district",
}


def normalize_indic_phonetics(text: str) -> str:
    """
    Normalizes phonetic variations and replaces colloquial Romanized keywords
    with canonical concepts to aid schema linking.
    """
    normalized = text.lower()
    for roman_token, canonical in TRANSLITERATION_MAP.items():
        # Match whole words only
        pattern = rf"\b{roman_token}\b"
        normalized = re.sub(pattern, f"{roman_token} ({canonical})", normalized)
    return normalized
