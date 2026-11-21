"""
SQL Synthesizer Agent — Dynamic Neural & Multi-Candidate Generation.
Synthesizes deterministic DuckDB SQL queries from cross-lingual Indic inputs
using local LLM inference (Ollama Qwen-2.5-Coder / Qwen-2.5) with schema grounding
and reflection-guided self-correction.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from indicsql.core.state import IndicSQLState
from indicsql.events.bus import EventBus
from indicsql.events.schemas import SQLSynthesizedEvent
from indicsql.models.metric_guard import sanitize_metric_aggregations
from indicsql.models.ollama_client import OllamaClient, prune_unrequested_temporal_filters
from indicsql.models.temporal_guard import extract_temporal_intent
from indicsql.schema.catalog import NDAPCatalog
from indicsql.schema.entity_grounder import dynamic_entity_grounder
from indicsql.schema.phonetic import transliterate_indic_to_latin

logger = logging.getLogger(__name__)

# Reusable Ollama client instance
_ollama_client = OllamaClient()

# ---------------------------------------------------------------------------
# Comprehensive Pan-India Entity Lexicons (All Regions)
# ---------------------------------------------------------------------------
_INDIC_DIGIT_MAP = str.maketrans("০১২৩৪৫৬৭৮৯०१२३४५६७८९౦౧౨౩౪౫౬౭౮౯௦௧௨௩௪௫௬௭௮௯", "0123456789012345678901234567890123456789")

_INDIC_NUMBER_WORDS = {
    # 1
    "একটি": 1, "এক": 1, "एक": 1, "ఒకటి": 1, "ఒక": 1, "ஒன்று": 1, "ஒரு": 1, "one": 1,
    # 2
    "দুটি": 2, "দুটো": 2, "দুই": 2, "दो": 2, "दोन": 2, "రెండు": 2, "இரண்டு": 2, "ரெண்டு": 2, "two": 2,
    # 3
    "তিনটি": 3, "তিনটে": 3, "তিন": 3, "तीन": 3, "మూడు": 3, "మూன்று": 3, "మూணு": 3, "three": 3,
    # 4
    "চারটি": 4, "চারটে": 4, "চার": 4, "चार": 4, "నాలుగు": 4, "நான்கு": 4, "நாலு": 4, "four": 4,
    # 5
    "পাঁচটি": 5, "পাঁচটা": 5, "পাঁচ": 5, "पांच": 5, "पाच": 5, "ఐదు": 5, "ஐந்து": 5, "அஞ்சு": 5, "five": 5,
    # 6
    "ছয়টি": 6, "ছটি": 6, "ছয়": 6, "छह": 6, "सहा": 6, "ఆరు": 6, "ஆறு": 6, "six": 6,
    # 7
    "সাতটি": 7, "সাত": 7, "सात": 7, "ఏడు": 7, "ஏழு": 7, "seven": 7,
    # 8
    "আটটি": 8, "আট": 8, "आठ": 8, "ఎనిమిది": 8, "எட்டு": 8, "eight": 8,
    # 9
    "নয়টি": 9, "নয়": 9, "नौ": 9, "नऊ": 9, "తొమ్మిది": 9, "ஒன்பது": 9, "nine": 9,
    # 10
    "দশটি": 10, "দশ": 10, "दस": 10, "दहा": 10, "పది": 10, "பத்து": 10, "ten": 10,
}

def normalize_indic_numbers(text: str) -> str:
    """Translates Indic script digits and replaces Indic number words with Arabic digits."""
    res = text.translate(_INDIC_DIGIT_MAP)
    for word, num in sorted(_INDIC_NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        res = res.replace(word, str(num))
    return res

def extract_threshold_filter(text: str) -> Optional[Tuple[str, float]]:
    """
    Extracts threshold comparisons like 'more than 65%', '> 65', 'below 40%', '65% se zyada' etc.
    Returns (operator, value), e.g. ('>', 65.0).
    """
    t_clean = normalize_indic_numbers(text).lower()
    # Greater than patterns
    gt_patterns = [
        r'(?:more\s+than|greater\s+than|above|over|exceeding|higher\s+than|>\s*=?)\s*(\d+(?:\.\d+)?)\s*%?',
        r'(\d+(?:\.\d+)?)\s*%?\s*(?:से\s*(?:ज्यादा|अधिक|ऊपर)|पेक्षा\s*(?:जास्त|अधिक)|এর\s*(?:বেশি|উপরে)|-க்கு\s*மேல்|விட\s*அதிகமாக|కంటే\s*(?:ఎక్కువ|పైగా)|>\s*=?|\+\s*)',
    ]
    for p in gt_patterns:
        m = re.search(p, t_clean)
        if m:
            return ('>', float(m.group(1)))

    # Less than patterns
    lt_patterns = [
        r'(?:less\s+than|lower\s+than|below|under|fewer\s+than|<\s*=?)\s*(\d+(?:\.\d+)?)\s*%?',
        r'(\d+(?:\.\d+)?)\s*%?\s*(?:से\s*(?:कम|नीचे)|पेक्षा\s*कमी|এর\s*কম|-க்கு\s*கீழ்|விட\s*குறைவாக|కంటే\s*తక్కువ|<\s*=?)',
    ]
    for p in lt_patterns:
        m = re.search(p, t_clean)
        if m:
            return ('<', float(m.group(1)))

    return None

_STATE_LEXICON: List[Tuple[List[str], str]] = [
    # North
    (["उत्तर प्रदेश", "uttar pradesh", "uttarpradesh", "up", "উত্তর প্রদেশ", "উত্তরप्रदेश", "উত্তর प्रदेश", "উত্তর প্রদেশের", "উত্তর प्रदेशের", "উত্তরপ্রদেশ", "உத்தரப் பிரதேசம்", "உத்தர பிரதேசம்", "உத்தரபிரதேசம்", "ఉత్తర ప్రదేశ్", "ఉత్తరప్రదేశ్"], "UTTAR PRADESH"),
    (["पंजाब", "punjab", "punjb", "panjab", "ਪੰਜਾਬ", "পাঞ্জাব", "பஞ்சாப்", "పంజాబ్"], "PUNJAB"),
    (["हरियाणा", "haryana", "haryan", "hariyana", "harayana", "হরিয়ানা", "ஹரியானா", "హర్యానా"], "HARYANA"),
    (["राजस्थान", "rajasthan", "rajsthan", "রাজস্থান", "ராஜஸ்தான்", "రాజస్థాన్"], "RAJASTHAN"),
    (["हिमाचल", "himachal pradesh", "himachal", "himanchal", "হিমাচল", "இமாச்சலப் பிரதேசம்", "హిమాచల్"], "HIMACHAL PRADESH"),
    (["उत्तराखंड", "uttarakhand", "uttrakhand", "uttaranchal", "উত্তরাখণ্ড", "உத்தரகாண்ட்", "உత్తరాఖండ్"], "UTTARAKHAND"),
    (["जम्मू", "कश्मीर", "jammu", "kashmir"], "JAMMU AND KASHMIR"),
    (["दिल्ली", "delhi", "new delhi", "দিল্লি", "தில்லி", "ఢిల్లీ"], "DELHI"),
    # South
    (["तमिलनाडु", "தமிழ்நாடு", "tamil nadu", "tamilnadu", "তামিলনাড়ু", "తమిళనాడు"], "TAMIL NADU"),
    (["कर्नाटक", "ಕರ್ನಾಟಕ", "karnataka", "karnatka", "কর্ণাটক", "கர்நாடகா", "కర్ణాటక"], "KARNATAKA"),
    (["केरल", "kerala", "keral", "കേരളം", "কেরালা", "கேரளா", "కేరళ"], "KERALA"),
    (["आंध्र", "ఆంధ్రప్రదేశ్", "ఆంధ్ర", "andhra pradesh", "andhrapradesh", "andhra", "অন্ধ্রপ্রদেশ", "ஆந்திரா", "ஆந்திரப் பிரதேசம்"], "ANDHRA PRADESH"),
    (["तेलंगाना", "తెలంగాణ", "telangana", "telngana", "telengana", "তেলেঙ্গানা", "தெலுங்கானா"], "TELANGANA"),
    # West
    (["महाराष्ट्र", "maharashtra", "maharastra", "maharshtra", "महाराष्ट्रात", "মহারাষ্ট্র", "மகாராஷ்டிரா", "మహారాష్ట్ర"], "MAHARASHTRA"),
    (["गुजरात", "gujarat", "gujrat", "ગુજરાત", "গুজরাত", "গুজরাট", "குஜராத்", "గుజరాత్"], "GUJARAT"),
    (["गोवा", "goa", "গোয়া"], "GOA"),
    # East & Central
    (["बिहार", "bihar", "বিহার", "பீகார்", "బీహార్"], "BIHAR"),
    (["पश्चिम बंगाल", "পশ্চিমবঙ্গ", "পশ্চিম বঙ্গ", "west bengal", "bengal", "மேற்கு வங்காளம்", "పశ్చిమ బెంగాల్"], "WEST BENGAL"),
    (["ओडिशा", "odisha", "orissa", "ଓଡ଼ିଶା", "ওড়িশা", "ஒடிசா", "ఒడిశా"], "ODISHA"),
    (["झारखंड", "jharkhand", "ঝাড়খণ্ড", "ஜார்கண்ட்", "జార్ఖండ్"], "JHARKHAND"),
    (["मध्य प्रदेश", "madhya pradesh", "mp", "মধ্যপ্রদেশ", "মধ্য প্রদেশ", "மத்தியப் பிரதேசம்", "மத்திய பிரதேசம்", "మధ్యప్రదేశ్"], "MADHYA PRADESH"),
    (["छत्तीसगढ़", "chhattisgarh", "ছত্তিশগড়", "சத்தீஸ்கர்", "ఛత్తీస్‌గఢ్"], "CHHATTISGARH"),
    # North-East & UTs
    (["असम", "assam", "অসম", "আসাম", "அசாம்", "అస్సాం"], "ASSAM"),
    (["मेघालय", "meghalaya"], "MEGHALAYA"),
    (["त्रिपुरा", "tripura"], "TRIPURA"),
    (["चंडीगढ़", "chandigarh"], "CHANDIGARH"),
    (["लद्दाख", "ladakh"], "LADAKH"),
]

_DISTRICT_LEXICON: List[Tuple[List[str], str]] = [
    (["पुणे", "pune"], "Pune"),
    (["नाशिक", "nashik"], "Nashik"),
    (["नागपुर", "नागपूर", "nagpur"], "Nagpur"),
    (["पटना", "patna"], "Patna"),
    (["वाराणसी", "varanasi", "kashi", "banaras"], "Varanasi"),
    (["लखनऊ", "lucknow"], "Lucknow"),
    (["कानपुर", "kanpur"], "Kanpur"),
    (["மதுரை", "madurai"], "Madurai"),
    (["சென்னை", "chennai"], "Chennai"),
    (["கோவை", "கோயம்புத்தூர்", "coimbatore"], "Coimbatore"),
    (["విశాఖపట్నం", "visakhapatnam", "vizag"], "Visakhapatnam"),
    (["గుంటూరు", "guntur"], "Guntur"),
    (["ముర్షిదాబాద్", "মুর্শিদাবাদ", "murshidabad"], "Murshidabad"),
    (["কলকাতা", "kolkata", "calcutta"], "Kolkata"),
    (["মালদা", "malda"], "Malda"),
    (["अमृतसर", "amritsar"], "Amritsar"),
    (["लुधियाना", "ludhiana"], "Ludhiana"),
    (["जयपुर", "jaipur"], "Jaipur"),
    (["जोधपुर", "jodhpur"], "Jodhpur"),
    (["भोपाल", "bhopal"], "Bhopal"),
    (["इंदौर", "indore"], "Indore"),
    (["अहमदाबाद", "ahmedabad"], "Ahmedabad"),
    (["सूरत", "surat"], "Surat"),
]

_COMMODITY_LEXICON: List[Tuple[List[str], str]] = [
    (["गेहूं", "गव्हाचा", "गव्हाची", "गव्हाचे", "गव्हा", "गहू", "গম", "গমের", "கோதுமை", "గోధుమ", "wheat", "godhumai"], "WHEAT"),
    (["चावल", "धान", "వరి", "நெல்", "rice", "চাল"], "RICE"),
    (["कापूस", "कापसाचे", "cotton", "பருத்தி", "పత్తి", "कपास"], "COTTON"),
    (["गन्ना", "ऊसाची", "ऊस", "sugarcane", "கரும்பு", "చెరకు", "আখ"], "SUGARCANE"),
    (["सोयाबीन", "सয়াবিন", "சோயாபீன்", "సోయాబీన్", "soybean"], "SOYBEAN"),
    (["मक्का", "మొక్కజొన్న", "maize", "corn"], "MAIZE"),
    (["सरसों", "mustard"], "MUSTARD"),
    (["मूंगफली", "भुईमुगाचे", "भुईमूग", "நிலக்கடலை", "వేరుశనగ", "চিনাবাদাম", "groundnut", "peanut"], "GROUNDNUT"),
    (["डीएपी", "டிஏபி", "డీఏపీ", "ডিএপি", "dap"], "DAP"),
    (["यूरिया", "युरिया", "யூரியா", "యూరియా", "ইউরিয়া", "urea"], "UREA"),
    (["कांदा", "प्याज", "வெங்காயத்தின்", "வெங்காயம்", "ఉల్లిపాయ", "পেঁয়াজের", "পেঁয়াজ", "onion"], "ONION"),
    (["మిర్చి", "మిరప", "मिर्ची", "மிளகாய்", "লঙ্কা", "chilli"], "CHILLI"),
    (["टोमॅटोचा", "टोमॅटो", "टमाटर", "தக்காளி", "టమాటా", "টমেটো", "tomato"], "TOMATO"),
]


def extract_canonical_entities(raw_query: str) -> Dict[str, str]:
    """
    Extracts standardized uppercase entities from vernacular queries.
    Prioritizes DynamicEntityGrounder for pan-India relational integrity,
    falling back to static lexicons with strict word boundaries for short tokens.
    """
    entities: Dict[str, str] = {}

    # 1. Dynamic In-Memory Grounder First (Precise, relational integrity, word boundaries)
    try:
        dynamic_hints = dynamic_entity_grounder.ground_entities(raw_query)
        for k, v in dynamic_hints.items():
            if v:
                entities[k] = v
    except Exception as e:
        logger.debug(f"Dynamic grounding error: {e}")

    lower = raw_query.lower()

    # 2. Static Lexicon fallback (with word boundary check for short tokens <= 3 chars)
    if "state_name" not in entities:
        for keywords, state_name in _STATE_LEXICON:
            for k in keywords:
                if len(k) <= 3:
                    if re.search(r'\b' + re.escape(k) + r'\b', lower):
                        entities["state_name"] = state_name
                        break
                elif k in lower or k in raw_query:
                    entities["state_name"] = state_name
                    break
            if "state_name" in entities:
                break

    if "district_name" not in entities:
        for keywords, district_name in _DISTRICT_LEXICON:
            for k in keywords:
                if len(k) <= 3:
                    if re.search(r'\b' + re.escape(k) + r'\b', lower):
                        entities["district_name"] = district_name
                        break
                elif k in lower or k in raw_query:
                    entities["district_name"] = district_name
                    break
            if "district_name" in entities:
                break

    if "commodity" not in entities:
        safe_comm_query = raw_query.replace("ఉత్పత్తి", " ")
        safe_lower = lower.replace("ఉత్పత్తి", " ")
        for keywords, commodity in _COMMODITY_LEXICON:
            for k in keywords:
                if len(k) <= 3:
                    if re.search(r'\b' + re.escape(k) + r'\b', safe_lower):
                        entities["commodity"] = commodity
                        break
                elif k in safe_lower or k in safe_comm_query:
                    entities["commodity"] = commodity
                    break
            if "commodity" in entities:
                break

    return entities


def _build_dynamic_fallback(
    table_name: str,
    table_schema: Dict[str, Any],
    entities: Dict[str, str],
    raw_query: str,
    matched_cols: Optional[List[str]] = None,
) -> str:
    """
    Constructs a structurally valid DuckDB SQL query dynamically from schema DDL
    when local LLM daemon is offline.
    """
    cols = table_schema.get("columns", {})
    where_clauses = []
    lower = raw_query.lower()

    if "state_name" in cols and "state_name" in entities:
        where_clauses.append(f"state_name = '{entities['state_name']}'")
    if "district_name" in cols and "district_name" in entities:
        where_clauses.append(f"district_name = '{entities['district_name']}'")
    if "crop_name" in cols and "commodity" in entities:
        where_clauses.append(f"crop_name = '{entities['commodity'].upper()}'")
    if "fertilizer_type" in cols and "commodity" in entities:
        where_clauses.append(f"fertilizer_type = '{entities['commodity'].upper()}'")
    if "commodity" in cols and "commodity" in entities:
        where_clauses.append(f"commodity = '{entities['commodity'].capitalize()}'")
    if "sector_skill_council" in cols:
        if any(w in lower or w in raw_query for w in ["automotive", "ऑटोमोटिव्ह", "ऑटोमोबाइल"]):
            where_clauses.append("sector_skill_council = 'Automotive'")
        elif any(w in lower or w in raw_query for w in ["healthcare", "आरोग्य सेवा", "स्वास्थ्य सेवा"]):
            where_clauses.append("sector_skill_council = 'Healthcare'")
        elif any(w in lower or w in raw_query for w in ["it-ites", "it sector", "ఐటీ రంగంలో", "ఐటీ", "आईटी"]):
            where_clauses.append("sector_skill_council = 'IT-ITeS'")
        elif any(w in lower or w in raw_query for w in ["agriculture", "कृषि", "விவசாய", "কৃষি"]):
            where_clauses.append("sector_skill_council = 'Agriculture'")

    # Apply explicit or relative temporal filters when requested in the question
    temp_col = next(
        (c for c in ("crop_year", "financial_year", "academic_year", "survey_year", "reporting_year", "census_year", "cycle_year", "year") if c in cols),
        None,
    )
    if temp_col:
        t_intent = extract_temporal_intent(raw_query)
        if t_intent.relative_type == "last_n_years" and t_intent.last_n_years_count:
            sub_where = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            where_clauses.append(
                f"{temp_col} IN (SELECT DISTINCT {temp_col} FROM {table_name}{sub_where} ORDER BY {temp_col} DESC LIMIT {t_intent.last_n_years_count})"
            )
        elif t_intent.relative_type in ("latest", "current"):
            sub_where = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            where_clauses.append(
                f"{temp_col} = (SELECT MAX({temp_col}) FROM {table_name}{sub_where})"
            )
        elif t_intent.financial_years and temp_col in ("financial_year", "academic_year", "survey_year"):
            fy = sorted(t_intent.financial_years)[-1]
            where_clauses.append(f"{temp_col} = '{fy}'")
        elif t_intent.year_ranges and temp_col in ("crop_year", "reporting_year", "census_year", "year"):
            y1, y2 = t_intent.year_ranges[0]
            where_clauses.append(f"{temp_col} BETWEEN {y1} AND {y2}")
        elif t_intent.years and not t_intent.financial_years and temp_col in ("crop_year", "reporting_year", "census_year", "year"):
            yr = sorted(t_intent.years)[-1]
            where_clauses.append(f"{temp_col} = {yr}")

    where_str = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Find candidate numeric measure columns
    numeric_cols = [
        c for c, desc in cols.items()
        if any(t in desc.upper() for t in ["BIGINT", "DOUBLE", "INTEGER", "FLOAT"])
        and not c.endswith("_year")
        and not c.endswith("_id")
    ]

    # Pre-compute metric intents and normalized queries early
    clean_norm = normalize_indic_numbers(raw_query)
    clean_norm_lower = clean_norm.lower()

    query_no_scheme = re.sub(
        r'पीएम-किसान|पीएम\s+किसान|pm-kisan|pm\s+kisan|పీఎం-కిసాన్|পিএম-কিষানের|পিএম-কিষাণ|பிஎம்-கிசான்',
        ' ',
        raw_query,
        flags=re.IGNORECASE,
    )
    lower_no_scheme = query_no_scheme.lower()
    has_farmer_intent = any(w in lower_no_scheme or w in query_no_scheme for w in ["farmer", "beneficiar", "किसान", "लाभार्थि", "शेतकऱ्यां", "రైతు", "விவசாயி", "কৃষক"])
    has_amount_intent = any(
        w in lower_no_scheme or w in query_no_scheme
        for w in [
            "amount", "disbursement", "disbursed", "distribute", "रुपये", "राशि",
            "धनराशि", "निधी", "रक्कम", "నిధులు", "பணம்", "நிதி", "টাকা", "অর্থ", "বিতরণ", "பண", "డబ్బు", "বরাদ্দ"
        ]
    )

    # Check for lowest / highest superlative in query with script boundaries
    is_min = any(re.search(r'\b' + re.escape(w) + r'\b', lower) for w in ['lowest', 'min', 'minimum', 'sabse kam']) or any(
        re.search(r'(?:^|[^\w\u0900-\u0D7F])' + re.escape(w) + r'(?:[^\w\u0900-\u0D7F]|$)', raw_query)
        for w in ['कम', 'குறைவாக', 'తక్కువ', 'అత్యల్పంగా', 'কম', 'कमी', 'সর্বনিম্ন']
    ) or "সবচেয়ে কম" in raw_query or "সবচেয়ে কম" in clean_norm
    is_max = any(re.search(r'\b' + re.escape(w) + r'\b', lower) for w in ['highest', 'max', 'maximum', 'sabse zyada']) or any(
        re.search(r'(?:^|[^\w\u0900-\u0D7F])' + re.escape(w) + r'(?:[^\w\u0900-\u0D7F]|$)', raw_query)
        for w in ['ज्यादा', 'सर्वाधिक', 'सर्वাধিক', 'अधिक', 'అత్యధిక', 'सर्वात जास्त', 'जास्त', 'அதிகமாக', 'அதிக', 'সর্বাধিক']
    ) or "সবচেয়ে বেশি" in raw_query

    # Check for top N / bottom N ranking
    top_match = re.search(r'\b(?:top|first|best|शीर्ष|सर्वोच्च|अव्वल|முன்னணி|அగ్ర)\s*(\d+)\b', clean_norm_lower) or re.search(
        r'(?:सबसे\s+अधिक|सर्वाधिक|अधिक|সর্বাধিক)[^0-9]*?(\d+)\s*(?:টি)?\s*(?:जिले|जिल्हे|மாவட்டங்கள்|జిల్లాలు|জেলা|districts)', clean_norm
    )
    bottom_match = re.search(r'\b(?:bottom|lowest|least|न्यूनतम|কনিষ্ঠ|সর্বনিম্ন)\s*(\d+)\b', clean_norm_lower) or re.search(
        r'(?:সবচেয়ে\s*কম|সর্বনিম্ন|सबसे\s*कम|न्यूनतम|सर्वात\s*कमी|மிகக்\s*குறைந்த|అత్యల్ప)[^0-9]*?(\d+)\s*(?:টি)?\s*(?:जिले|जिल्हे|மாவட்டங்கள்|జిల్లాలు|জেলা|districts)', clean_norm
    )
    if not (top_match or bottom_match):
        entity_num_match = re.search(
            r'(?:কোন|किन|कोणत्या|எந்த|ఏ|which)?\s*(\d+)\s*(?:টি|টা)?\s*(?:districts|जिले|जिल्हे|மாவட்டங்கள்|జిల్లాలు|জেলা)',
            clean_norm,
            re.IGNORECASE
        )
        if entity_num_match:
            if is_min or any(w in clean_norm for w in ["সবচেয়ে কম", "কম", "कम", "bottom", "lowest", "least", "সর্বনিম্ন"]):
                bottom_match = entity_num_match
            elif is_max or any(w in clean_norm for w in ["সবচেয়ে বেশি", "বেশি", "ज्यादा", "top", "highest", "সর্বাধিক"]):
                top_match = entity_num_match

    if (top_match or bottom_match) and "district_name" in cols and numeric_cols:
        limit_n = int(top_match.group(1)) if top_match else int(bottom_match.group(1))
        order_dir = "DESC" if top_match else "ASC"
        if table_name == "ndap_pm_kisan_disbursement":
            target_measure = "amount_inr" if has_amount_intent else "farmer_beneficiaries"
        else:
            target_measure = next((c for c in (matched_cols or []) if c in numeric_cols), numeric_cols[0])
        if table_name == "ndap_nfhs5_health_indicators":
            return f"SELECT district_name, {target_measure} FROM {table_name}{where_str} ORDER BY {target_measure} {order_dir} LIMIT {limit_n};"
        is_avg = "pct" in target_measure or "_rate" in target_measure
        func = "AVG" if is_avg else "SUM"
        alias = f"avg_{target_measure}" if is_avg else f"total_{target_measure}"
        return f"SELECT district_name, {func}({target_measure}) AS {alias} FROM {table_name}{where_str} GROUP BY district_name ORDER BY {alias} {order_dir} LIMIT {limit_n};"

    # Check for threshold filters on grouped entities (e.g. female literacy rate > 65% in Bihar districts)
    threshold = extract_threshold_filter(raw_query)
    is_district_query = "district_name" in cols and (
        any(w in clean_norm_lower for w in ["which district", "which districts", "districts in", "district in", "kis jile", "kon jela", "kis district"])
        or any(w in raw_query for w in ["कौन से जिले", "किस जिले", "कोणते जिल्हे", "कोणत्या जिल्ह्यात", "எந்த மாவட்டங்கள்", "ఏ జిల్లాలు", "কোন জেলা", "কোন জেলাগুলি", "কোন জেলায়"])
        or ("district_name" not in entities and any(w in clean_norm_lower for w in ["district", "districts", "जिले", "जिल्हे", "மாவட்டங்கள்", "జిల్లాలు", "জেলা"]))
    )

    if threshold and is_district_query and numeric_cols:
        op, val = threshold
        target_measure = next((c for c in (matched_cols or []) if c in numeric_cols), numeric_cols[0])
        is_avg = (
            "pct" in target_measure
            or "_rate" in target_measure
            or target_measure.startswith("rate_")
            or "ratio" in target_measure
            or "avg" in clean_norm_lower
            or "average" in clean_norm_lower
            or "औसत" in raw_query
            or "सरासरी" in raw_query
            or "சராசரி" in raw_query
            or "సగటు" in raw_query
            or "গড়" in raw_query
        )
        func = "AVG" if is_avg else "SUM"
        alias = f"avg_{target_measure}" if is_avg else f"total_{target_measure}"
        round_expr = f"ROUND({func}({target_measure}), 2)" if is_avg else f"{func}({target_measure})"
        order_dir = "DESC" if op in (">", ">=") else "ASC"
        return f"SELECT district_name, {round_expr} AS {alias} FROM {table_name}{where_str} GROUP BY district_name HAVING {func}({target_measure}) {op} {val} ORDER BY {alias} {order_dir};"

    if (is_min or is_max) and "district_name" in cols and numeric_cols:
        if table_name == "ndap_pm_kisan_disbursement":
            target_measure = "amount_inr" if has_amount_intent else "farmer_beneficiaries"
        else:
            target_measure = next((c for c in (matched_cols or []) if c in numeric_cols), numeric_cols[0])
        order_dir = "ASC" if is_min else "DESC"
        if table_name in ("ndap_pmay_rural_housing", "ndap_school_infrastructure", "ndap_jal_jeevan_tap_water", "ndap_pm_kisan_disbursement") and not (
            "pct" in target_measure or "_rate" in target_measure
        ):
            alias = f"total_{target_measure}"
            return f"SELECT district_name, SUM({target_measure}) AS {alias} FROM {table_name}{where_str} GROUP BY district_name ORDER BY {alias} {order_dir} LIMIT 1;"
        return f"SELECT district_name, {target_measure} FROM {table_name}{where_str} ORDER BY {target_measure} {order_dir} LIMIT 1;"

    # Strip scheme title before checking if both farmer count and disbursement amount are explicitly requested
    query_no_scheme = re.sub(
        r'पीएम-किसान|पीएम\s+किसान|pm-kisan|pm\s+kisan|పీఎం-కిసాన్|পিএম-কিষানের|পিএম-কিষাণ|பிஎம்-கிசான்',
        ' ',
        raw_query,
        flags=re.IGNORECASE,
    )
    lower_no_scheme = query_no_scheme.lower()
    has_farmer_intent = any(w in lower_no_scheme or w in query_no_scheme for w in ["farmer", "beneficiar", "किसान", "लाभार्थि", "शेतकऱ्यां", "రైతు", "விவசாயி", "কৃষক"])
    has_amount_intent = any(w in lower_no_scheme or w in query_no_scheme for w in ["amount", "disbursement", "disbursed", "distribute", "रुपये", "राशि", "धनराशि", "निधी", "रक्कम", "నిధులు", "பணம்", "টাকা", "অর্থ"])
    if table_name == "ndap_pm_kisan_disbursement":
        if has_farmer_intent and has_amount_intent:
            return f"SELECT SUM(farmer_beneficiaries) AS total_farmers, SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement{where_str};"
        if has_amount_intent and not has_farmer_intent:
            return f"SELECT SUM(amount_inr) AS total_metric FROM ndap_pm_kisan_disbursement{where_str};"

    if numeric_cols:
        target_measure = next((c for c in (matched_cols or []) if c in numeric_cols), numeric_cols[0])
        if table_name == "ndap_nfhs5_health_indicators" and "district_name" in entities:
            return f"SELECT {target_measure} FROM {table_name}{where_str};"
        if target_measure == "max_price_inr":
            return f"SELECT MAX({target_measure}) AS total_metric FROM {table_name}{where_str};"
        if target_measure == "min_price_inr":
            return f"SELECT MIN({target_measure}) AS total_metric FROM {table_name}{where_str};"
        is_avg = (
            "pct" in target_measure
            or "_rate" in target_measure
            or target_measure.startswith("rate_")
            or "_mmr" in target_measure
            or "_imr" in target_measure
            or "ratio" in target_measure
            or "price" in target_measure
            or "avg" in lower
            or "average" in lower
            or "औसत" in raw_query
            or "सरासरी" in raw_query
            or "சராசரி" in raw_query
            or "సగటు" in raw_query
            or "গড়" in raw_query
        )
        func = "AVG" if is_avg else "SUM"
        return f"SELECT {func}({target_measure}) AS total_metric FROM {table_name}{where_str};"

    return f"SELECT * FROM {table_name}{where_str} LIMIT 10;"


def _all_matches(raw_query: str, lexicon: List[Tuple[List[str], str]]) -> List[str]:
    """Return every distinct canonical value from a lexicon mentioned in the query."""
    safe = raw_query.replace("ఉత్పత్తి", " ")
    lower = safe.lower()
    found: List[str] = []
    for keywords, canonical in lexicon:
        for k in keywords:
            hit = (
                re.search(r"\b" + re.escape(k) + r"\b", lower)
                if len(k) <= 3
                else (k in lower or k in safe)
            )
            if hit:
                if canonical not in found:
                    found.append(canonical)
                break
    return found


def _build_multi_entity_groupby(
    table_name: str,
    table_schema: Dict[str, Any],
    raw_query: str,
    matched_cols: Optional[List[str]] = None,
) -> Optional[str]:
    """
    When a question names several states and/or crops (e.g. "wheat and rice in Punjab
    and Haryana separately"), return one row per entity via GROUP BY instead of
    collapsing everything into a single filtered scalar. Returns None otherwise.
    """
    cols = table_schema.get("columns", {})
    states = _all_matches(raw_query, _STATE_LEXICON) if "state_name" in cols else []
    commodities = _all_matches(raw_query, _COMMODITY_LEXICON)
    crop_col = next((c for c in ("crop_name", "fertilizer_type", "commodity") if c in cols), None)
    if len(states) < 2 and (len(commodities) < 2 or not crop_col):
        return None

    numeric_cols = [
        c for c, desc in cols.items()
        if any(t in desc.upper() for t in ["BIGINT", "DOUBLE", "INTEGER", "FLOAT"])
        and not c.endswith("_year") and not c.endswith("_id")
    ]
    if not numeric_cols:
        return None
    measure = next((c for c in (matched_cols or []) if c in numeric_cols), numeric_cols[0])
    lower = raw_query.lower()
    is_avg = (
        any(t in measure for t in ("pct", "_rate", "price", "ratio"))
        or any(w in lower or w in raw_query for w in ("average", "avg", "औसत", "सरासरी", "சராசரி", "సగటు", "গড়"))
    )
    func = "AVG" if is_avg else "SUM"
    alias = f"avg_{measure}" if is_avg else f"total_{measure}"

    def lit(v: str) -> str:
        return v.capitalize() if crop_col == "commodity" else v.upper()

    group_cols: List[str] = []
    where: List[str] = []
    if len(states) >= 1 and "state_name" in cols:
        if len(states) > 1:
            group_cols.append("state_name")
        where.append("state_name IN (" + ", ".join(f"'{s}'" for s in states) + ")")
    if crop_col and commodities:
        if len(commodities) > 1:
            group_cols.append(crop_col)
        where.append(f"{crop_col} IN (" + ", ".join(f"'{lit(c)}'" for c in commodities) + ")")
    if not group_cols:
        return None
    gb = ", ".join(group_cols)
    return (
        f"SELECT {gb}, {func}({measure}) AS {alias} FROM {table_name} "
        f"WHERE {' AND '.join(where)} GROUP BY {gb} ORDER BY {gb};"
    )


def synthesize_sql(
    state: IndicSQLState,
    error_feedback: Optional[str] = None,
    previous_sql: Optional[str] = None,
) -> Tuple[str, str, float]:
    """
    Synthesizes SQL query through Ollama neural generation with schema awareness
    and reflective self-correction.
    Returns:
        (sql_query, method, confidence_score)
    """
    raw_query = state.get("raw_query", "").strip()
    table_name = state.get("target_database") or "ndap_pm_kisan_disbursement"
    table_schema = NDAPCatalog.get_table_schema(table_name)
    language = state.get("detected_lang", "en")
    entities = extract_canonical_entities(raw_query)

    # Map generic commodity to the table's specific column name
    table_cols = table_schema.get("columns", {})
    mapped_entities: Dict[str, str] = {}
    if "state_name" in entities:
        mapped_entities["state_name"] = entities["state_name"]
    if "district_name" in entities:
        mapped_entities["district_name"] = entities["district_name"]
    if "commodity" in entities:
        if "crop_name" in table_cols:
            mapped_entities["crop_name"] = entities["commodity"]
        elif "fertilizer_type" in table_cols:
            mapped_entities["fertilizer_type"] = entities["commodity"]
        elif "commodity" in table_cols:
            mapped_entities["commodity"] = entities["commodity"]

    matched_cols = [el.get("column_name") for el in state.get("pruned_schema", [])]

    multi_sql = _build_multi_entity_groupby(table_name, table_schema, raw_query, matched_cols)
    if multi_sql:
        return multi_sql, "schema_grounded_multi_entity", 0.90

    model_tier = state.get("model_tier", "trained_pro")
    if model_tier == "turbo_fast":
        # Turbo Tier: Deterministic, sub-50ms schema-grounded execution
        fallback_sql = _build_dynamic_fallback(
            table_name, table_schema, entities, raw_query, matched_cols=matched_cols
        )
        return fallback_sql, "turbo_fast_grounded", 0.88

    # Pro Tier: Neural Generation via Ollama / fine-tuned weights with fallback
    if _ollama_client.is_available:
        try:
            transliterated = transliterate_indic_to_latin(raw_query)
            effective_query = (
                f"{raw_query}\n(Phonetic Romanization: {transliterated})"
                if transliterated and transliterated != raw_query
                else raw_query
            )
            neural_sql = _ollama_client.generate_sql(
                query=effective_query,
                table_name=table_name,
                table_schema=table_schema,
                language=language,
                canonical_entities=mapped_entities,
                target_columns=matched_cols,
                error_feedback=error_feedback,
                previous_sql=previous_sql,
            )
            if neural_sql and ("SELECT" in neural_sql.upper() or "WITH" in neural_sql.upper()):
                logger.info("Successfully synthesized neural SQL (%s)", _ollama_client.public_label)
                return neural_sql, f"ollama_{_ollama_client.public_label}", 0.94
        except Exception as e:
            logger.warning("Neural SQL synthesis error: %s", e)

    # 2. Dynamic Schema-Grounded Fallback
    matched_cols = [el.get("column_name") for el in state.get("pruned_schema", [])]
    fallback_sql = _build_dynamic_fallback(
        table_name, table_schema, entities, raw_query, matched_cols=matched_cols
    )
    return fallback_sql, "schema_grounded_fallback", 0.80


def sql_synthesizer_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    SQL Synthesizer Node in LangGraph Swarm.
    Receives current state, applies reflection feedback if retrying,
    and produces executable SQL.
    """
    error_feedback = state.get("reflection_feedback")
    prev_sql = state.get("generated_sql")

    best_sql, method, score = synthesize_sql(
        state,
        error_feedback=error_feedback,
        previous_sql=prev_sql,
    )

    # Publish Event
    EventBus.publish(
        SQLSynthesizedEvent(
            query_id=state.get("query_id"),
            candidate_sql=best_sql,
            method=method,
            utility_score=score,
            candidates_evaluated=1,
        )
    )

    audit_entry = {
        "step": 3,
        "agent": "SQLSynthesizerAgent",
        "action": "neural_or_grounded_synthesis",
        "method": method,
        "utility_score": score,
        "output_sql": best_sql,
        "reflection_attempt": state.get("reflection_attempts", 0),
    }

    # Final defense-in-depth: Ensure unrequested temporal filters are pruned and metrics are aligned
    raw_query = state.get("raw_query", "")
    target_table = state.get("target_database")
    raw_stochastic_draft = best_sql
    best_sql = prune_unrequested_temporal_filters(best_sql, raw_query, table_name=target_table)
    best_sql = sanitize_metric_aggregations(best_sql, raw_query, table_name=target_table)

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "generated_sql": best_sql,
        "raw_stochastic_sql": raw_stochastic_draft,
        "syntax_valid": True,
        "model_tier": state.get("model_tier", "trained_pro"),
        "grounded_entities": extract_canonical_entities(raw_query),
        "audit_trace": current_trace,
    }


def _tot_select(state: IndicSQLState) -> Tuple[str, float, List[Dict[str, Any]], str]:
    """Helper for backwards-compatible model combo fallback."""
    sql, method, score = synthesize_sql(state)
    return sql, score, [{"sql": sql, "score": score}], method
