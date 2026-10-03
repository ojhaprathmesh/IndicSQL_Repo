import re
from typing import Dict, Optional

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate

    HAS_SANSCRIPT = True
except ImportError:
    HAS_SANSCRIPT = False

# Mapping from language code to sanscript output scheme
LANG_TO_SCHEME: Dict[str, str] = (
    {
        "hi": "devanagari",
        "mr": "devanagari",
        "bn": "bengali",
        "ta": "tamil",
        "te": "telugu",
        "gu": "gujarati",
    }
    if HAS_SANSCRIPT
    else {}
)

# Common Latin-to-canonical mappings for Indian administrative terms
TRANSLITERATION_MAP: Dict[str, str] = {
    "kisan": "farmer",
    "kisano": "farmer",
    "shatkari": "farmer",
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
    "manrega": "mgnrega",
}


def normalize_indic_phonetics(text: str, target_lang: Optional[str] = "hi") -> str:
    """
    Normalizes phonetic variations and replaces colloquial Romanized keywords
    with canonical concepts to aid schema linking.

    If target_lang is provided and Latin characters are present, performs
    transliteration into the target Indic script when indic-transliteration is installed.
    """
    normalized = text.lower()
    for roman_token, canonical in TRANSLITERATION_MAP.items():
        pattern = rf"\b{roman_token}\b"
        normalized = re.sub(pattern, f"{roman_token} ({canonical})", normalized)

    # If sanscript is available, transliterate Latin phonetic tokens to Indic script
    if HAS_SANSCRIPT and target_lang and target_lang in LANG_TO_SCHEME:
        scheme = getattr(sanscript, LANG_TO_SCHEME[target_lang].upper(), None)
        if scheme and any(c.isascii() and c.isalpha() for c in text):
            # Keep both original/canonical mapping and transliterated terms
            try:
                xlit = transliterate(text, sanscript.ITRANS, scheme)
                return f"{normalized} {xlit}".strip()
            except Exception:
                return normalized

    return normalized
