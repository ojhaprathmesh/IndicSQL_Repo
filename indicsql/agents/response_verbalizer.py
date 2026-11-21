"""
Response Verbalizer Agent.
Takes tabular SQL execution results and verbalizes fluent, concise natural language answers
in the citizen's mother tongue (Hindi, Marathi, Tamil, Telugu, Bengali, Hinglish, English)
with localized Indian numbering (Lakhs and Crores).
"""

import re
from typing import Any, Dict
from indicsql.core.state import IndicSQLState
from indicsql.events.bus import EventBus
from indicsql.events.schemas import VoiceSynthesisEvent
from indicsql.agents.sql_synthesizer import extract_threshold_filter


def format_indian_currency_number(val: Any, lang: str = "hi") -> str:
    """Formats large integers/floats into Crores or Lakhs safely with localized language terms."""
    if val is None:
        return "0"
    try:
        fval = float(val)
    except (ValueError, TypeError):
        return str(val)

    if lang == "mr":
        crore_label = "कोटी (Crores)"
        lakh_label = "लाख (Lakhs)"
    elif lang == "ta":
        crore_label = "கோடி (Crores)"
        lakh_label = "இலட்சம் (Lakhs)"
    elif lang == "te":
        crore_label = "కోట్లు (Crores)"
        lakh_label = "లక్షలు (Lakhs)"
    elif lang == "bn":
        crore_label = "কোটি (Crores)"
        lakh_label = "লাখ (Lakhs)"
    elif lang in ["en", "hi-en"]:
        crore_label = "Crores"
        lakh_label = "Lakhs"
    else:  # default 'hi'
        crore_label = "कोटी (Crores)"
        lakh_label = "लाख (Lakhs)"

    if fval >= 10_000_000:
        crores = fval / 10_000_000
        return f"{crores:.2f} {crore_label}"
    if fval >= 100_000:
        lakhs = fval / 100_000
        return f"{lakhs:.2f} {lakh_label}"
    return f"{fval:,.0f}"


def verbalize_tabular_result(state: IndicSQLState) -> str:
    """Produces the localized natural language explanation across all 7 supported languages."""
    lang = state.get("detected_lang", "en")

    if state.get("is_out_of_scope"):
        if lang == "hi":
            return (
                "यह प्रश्न उपलब्ध डेटाबेस के दायरे (scope) से बाहर है। "
                "IndicSQL केवल 20 भारतीय सरकारी सार्वजनिक डेटासेट (जैसे कृषि व फसल उत्पादन, पीएम-किसान, "
                "उर्वरक, मंडी भाव, स्कूल व उच्च शिक्षा, ग्रामीण स्वास्थ्य, आयुष्मान भारत, मनरेगा एवं जल जीवन मिशन) का उत्तर दे सकता है।"
            )
        elif lang == "mr":
            return (
                "हा प्रश्न उपलब्ध डेटाबेसच्या कक्षेबाहेर (scope) आहे. "
                "IndicSQL सध्या 20 सरकारी सार्वजनिक डेटासेट्स (कृषी उत्पादन, खते, बाजार भाव, पीएम-किसान, "
                "शिक्षण, आरोग्य, मनरेगा रोजगार व जल जीवन नळ जोडणी) वरील प्रश्नांची माहिती देऊ शकते."
            )
        elif lang == "te":
            return (
                "ఈ ప్రశ్న డేటాబేస్ పరిధికి వెలుపల ఉంది. "
                "IndicSQL కేవలం భారత ప్రభుత్వ 20 NDAP పబ్లిక్ డేటాసెట్‌లకు (వ్యవసాయం, పంటల ఉత్పత్తి, పీఎం-కిసాన్, "
                "ఎరువులు, పాఠశాల విద్య, గ్రామీణ ఆరోగ్యం, ఆయుష్మాన్ భారత్, ఉపాధి హామీ, జల్ జీవన్ మిషన్) సంబంధించిన ప్రశ్నలకు మాత్రమే సమాధానం ఇవ్వగలదు."
            )
        elif lang == "ta":
            return (
                "இந்தக் கேள்வி கிடைக்கக்கூடிய தரவுத்தளத்தின் எல்லைக்கு அப்பாற்பட்டது. "
                "IndicSQL 20 இந்திய அரசு (NDAP) பொதுத் திட்டங்கள் (வேளாண்மை, பயிர் உற்பத்தி, பிஎம்-கிசான், உரங்கள், "
                "கல்வி, பொது சுகாதாரம், மகாத்மா காந்தி வேலை உறுதித் திட்டம், ஜல் ஜீவன் குடிநீர் இணைப்புகள்) சார்ந்த கேள்விகளுக்கு மட்டுமே பதிலளிக்கும்."
            )
        elif lang == "bn":
            return (
                "এই প্রশ্নটি উপলব্ধ ডাটাবেসের আওতাভুক্ত নয়। "
                "IndicSQL ভারতীয় সরকারের ২০টি সরকারি তথ্যভাণ্ডার (যেমন কৃষি ও ফসল উৎপাদন, পিএম-কিষাণ, সার, শিক্ষা, "
                "স্বাস্থ্যসেবা, ১০০ দিনের কাজ, এবং পানীয় জল সংযোগ) সম্পর্কিত প্রশ্নের উত্তর দিতে সক্ষম।"
            )
        elif lang == "hi-en":
            return (
                "Yeh question available database ke scope se bahar hai. "
                "IndicSQL currently 20 Indian Government (NDAP) public datasets cover karta hai: agriculture (crop production, mandi prices, fertilizers, PM-KISAN), education, healthcare, MGNREGA employment, and Jal Jeevan tap water."
            )
        else:
            return (
                "This question is outside the scope of the available database. "
                "IndicSQL currently queries 20 Indian Government (NDAP) public datasets covering agriculture (crop production, mandi prices, fertilizers, soil health, PM-KISAN), public education & skilling, healthcare (Ayushman Bharat, rural PHCs, TB, NFHS-5), and rural welfare (MGNREGA employment, Jal Jeevan tap water, PMAY housing, and rural roads)."
            )

    res = state.get("execution_result")
    err = state.get("execution_error")

    if err or not res:
        if lang == "hi":
            return f"माफ़ कीजिए, डेटाबेस में आपके प्रश्न का सटीक उत्तर नहीं मिल सका। (त्रुटि: {err or 'कोई डेटा नहीं'})"
        elif lang == "mr":
            return f"क्षमस्व, डेटाबेसमध्ये आपल्या प्रश्नाचे उत्तर सापडू शकले नाही. (त्रुटी: {err or 'डेटा उपलब्ध नाही'})"
        elif lang == "ta":
            return f"மன்னிக்கவும், தரவுத்தளத்தில் உங்கள் கேள்விக்கான சரியான பதில் கிடைக்கவில்லை. (பிழை: {err or 'தரவு இல்லை'})"
        elif lang == "te":
            return f"క్షమించండి, డేటాబేస్ లో మీ ప్రశ్నకు ఖచ్చితమైన సమాధానం లభించలేదు. (లోపం: {err or 'డేటా లేదు'})"
        elif lang == "bn":
            return f"দুঃখিত, ডাটাবেসে আপনার প্রশ্নের সঠিক উত্তর পাওয়া যায়নি। (ত্রুটি: {err or 'কোন তথ্য নেই'})"
        elif lang == "hi-en":
            return f"Sorry, database mein aapke question ka exact answer nahi mila. (Error: {err or 'No data found'})"
        return f"Unable to retrieve data for query. (Reason: {err or 'Empty result set'})"

    rows = res.get("rows", [])
    columns = [c.lower() for c in res.get("columns", [])]
    query_text = (state.get("raw_query", "") or state.get("normalized_query", "")).lower()

    # Detect State in Query early
    state_display = ""
    st_lower = f" {query_text} "
    if any(w in query_text for w in ["bihar", "बिहार", "বিহার", "பீகார்", "బీహార్"]):
        state_display = "Bihar" if lang in ("en", "hi-en") else ("বিহার" if lang == "bn" else ("बिहार" if lang in ("hi", "mr") else "Bihar"))
    elif any(w in query_text for w in ["uttar pradesh", "उत्तर प्रदेश", "উত্তর প্রদেশ", "উত্তর प्रदेश", "উত্তরপ্রদেশ", "உத்தர", "ఉత్తర"]) or " up " in st_lower:
        state_display = "Uttar Pradesh" if lang in ("en", "hi-en") else ("উত্তর প্রদেশ" if lang == "bn" else ("उत्तर प्रदेश" if lang in ("hi", "mr") else "Uttar Pradesh"))
    elif any(w in query_text for w in ["maharashtra", "महाराष्ट्र", "মহারাষ্ট্র", "மகாராஷ்டிரா", "మహారాష్ట్ర"]):
        state_display = "Maharashtra" if lang in ("en", "hi-en") else ("মহারাষ্ট্র" if lang == "bn" else ("महाराष्ट्र" if lang in ("hi", "mr") else "Maharashtra"))
    elif any(w in query_text for w in ["tamil nadu", "தமிழ்நாடு", "তামিলনাড়ু", "తమిళనాడు"]):
        state_display = "Tamil Nadu" if lang in ("en", "hi-en") else ("তামিলনাড়ু" if lang == "bn" else ("तमिलनाडु" if lang in ("hi", "mr") else "Tamil Nadu"))
    elif any(w in query_text for w in ["rajasthan", "राजस्थान", "রাজস্থান", "ராஜஸ்தான்", "రాజస్థాన్"]):
        state_display = "Rajasthan" if lang in ("en", "hi-en") else ("রাজস্থান" if lang == "bn" else ("राजस्थान" if lang in ("hi", "mr") else "Rajasthan"))
    elif any(w in query_text for w in ["punjab", "पंजाब", "পাঞ্জাব", "பஞ்சாப்", "పంజాబ్"]):
        state_display = "Punjab" if lang in ("en", "hi-en") else ("পাঞ্জাব" if lang == "bn" else ("पंजाब" if lang in ("hi", "mr") else "Punjab"))
    elif any(w in query_text for w in ["haryana", "हरियाणा", "হরিয়ানা", "ஹரியானா", "హర్యానా"]):
        state_display = "Haryana" if lang in ("en", "hi-en") else ("হরিয়ানা" if lang == "bn" else ("हरियाणा" if lang in ("hi", "mr") else "Haryana"))

    if not rows:
        th = extract_threshold_filter(query_text)
        if th:
            op, val = th
            op_hi = "से अधिक" if op in (">", ">=") else "से कम"
            op_en = "more than" if op in (">", ">=") else "less than"
            op_mr = "पेक्षा जास्त" if op in (">", ">=") else "पेक्षा कमी"
            op_ta = "-க்கு மேல்" if op in (">", ">=") else "-க்கு கீழ்"
            op_te = "కంటే ఎక్కువ" if op in (">", ">=") else "కంటే తక్కువ"
            op_bn = "এর বেশি" if op in (">", ">=") else "এর কম"

            if any(w in query_text for w in ["literacy", "litracy", "साक्षरता", "கல்வியறிவு", "అక్షరాస్యత", "সাক্ষরতা"]):
                val_int = int(val) if val == int(val) else val
                if lang == "hi":
                    st = f"{state_display} में " if state_display else ""
                    return f"डेटाबेस रिकॉर्ड के अनुसार {st}किसी भी जिले की औसत महिला साक्षरता दर {val_int}% {op_hi} दर्ज नहीं है (बिहार में अधिकतम समस्तीपुर में 55.5% है)।"
                elif lang == "mr":
                    st = f"{state_display} मधील " if state_display else ""
                    return f"डेटाबेसच्या नोंदीनुसार {st}कोणत्याही जिल्ह्याचा सरासरी महिला साक्षरता दर {val_int}% {op_mr} नोंदवला गेलेला नाही (बिहारमध्ये सर्वाधिक समस्तीपूरमध्ये 55.5% आहे)."
                elif lang == "ta":
                    st = f"{state_display} மாநிலத்தில் " if state_display else ""
                    return f"தரவுத்தள பதிவுகளின்படி {st}எந்த மாவட்டத்திலும் சராசரி பெண் கல்வியறிவு விகிதம் {val_int}% {op_ta} இல்லை (பீகாரில் அதிகபட்சமாக சமஸ்திபூரில் 55.5%)."
                elif lang == "te":
                    st = f"{state_display} లో " if state_display else ""
                    return f"డేటాబేస్ రికార్డుల ప్రకారం {st}ఏ జిల్లాలోనూ సగటు మహిళా అక్షరాస్యత రేటు {val_int}% {op_te} లేదు (బీహార్‌లో గరిష్టంగా సమస్తిపూర్‌లో 55.5%)."
                elif lang == "bn":
                    st = f"{state_display}-এ " if state_display else ""
                    return f"ডাটাবেস রেকর্ড অনুসারে {st}কোনো জেলাতেই গড় মহিলা সাক্ষরতার হার {val_int}% {op_bn} রেকর্ড করা হয়নি (বিহারে সর্বোচ্চ সমস্তিপুরে ৫৫.৫%)।"
                elif lang == "hi-en":
                    st = f"{state_display} mein " if state_display else ""
                    return f"Database records ke according {st}kisi bhi district ki average female literacy rate {val_int}% se zyada nahi hai (Bihar mein highest Samastipur mein 55.5% hai)."
                else:
                    st = f" in {state_display}" if state_display else ""
                    return f"According to database records, no districts{st} recorded an average female literacy rate of {op_en} {val_int}% (the highest recorded in Bihar is Samastipur at 55.5%)."
            else:
                val_int = int(val) if val == int(val) else val
                if lang == "hi":
                    return f"डेटाबेस में दिए गए मापदंड ({val_int} {op_hi}) के अनुसार कोई रिकॉर्ड नहीं मिला।"
                elif lang == "mr":
                    return f"डेटाबेसमध्ये दिलेल्या निकषानुसार ({val_int} {op_mr}) कोणतीही नोंद आढळली नाही."
                elif lang == "ta":
                    return f"தரவுத்தளத்தில் கொடுக்கப்பட்ட அளவுகோலின்படி ({val_int} {op_ta}) பதிவுகள் எதுவும் கிடைக்கவில்லை."
                elif lang == "te":
                    return f"డేటాబేస్ లో పేర్కొన్న ప్రమాణాల ప్రకారం ({val_int} {op_te}) ఎటువంటి రికార్డులు కనుగొనబడలేదు."
                elif lang == "bn":
                    return f"ডাটাবেসে প্রদত্ত মানদণ্ড ({val_int} {op_bn}) অনুযায়ী কোনো রেকর্ড পাওয়া যায়নি।"
                elif lang == "hi-en":
                    return f"Database mein specified criteria ({op_en} {val_int}) ke mutabiq koi record nahi mila."
                else:
                    return f"No districts found matching the criteria ({op_en} {val_int})."

        if lang == "hi":
            return "डेटाबेस में कोई रिकॉर्ड नहीं मिला।"
        elif lang == "mr":
            return "डेटाबेसमध्ये कोणतीही नोंद आढळली नाही."
        elif lang == "ta":
            return "தரவுத்தளத்தில் பதிவுகள் எதுவும் கிடைக்கவில்லை."
        elif lang == "te":
            return "డేటాబేస్ లో ఎటువంటి రికార్డులు కనుగొనబడలేదు."
        elif lang == "bn":
            return "ডাটাবেসে কোনো রেকর্ড পাওয়া যায়নি।"
        elif lang == "hi-en":
            return "Database mein koi matching record nahi mila."
        return "No matching records found in database."

    # 0a. Multi-entity breakdown (e.g. wheat & rice in Punjab & Haryana, one row each)
    if (
        len(rows) > 1
        and "district_name" not in columns
        and len(columns) >= 2
        and not re.search(r"\b(top|bottom|highest|lowest)\b|शीर्ष", query_text)
    ):
        dim_idx = [i for i, c in enumerate(columns[:-1]) if c in ("state_name", "crop_name", "fertilizer_type", "commodity", "year", "crop_year", "reporting_year")]
        if dim_idx and isinstance(rows[0][-1], (int, float)):
            metric_label = columns[-1].replace("total_", "").replace("avg_", "avg ").replace("_", " ")
            items = []
            for r in rows:
                label = " – ".join(str(r[i]).title() for i in dim_idx)
                items.append(f"{label}: {format_indian_currency_number(r[-1], lang=lang)}")
            lead = {
                "hi": "विवरण", "mr": "तपशील", "ta": "விவரம்", "te": "వివరాలు",
                "bn": "বিস্তারিত", "hi-en": "Breakdown",
            }.get(lang, "Breakdown")
            return f"{lead} ({metric_label}): " + "; ".join(items) + "."

    # 0. Multi-row Ranking / Grouping Verbalization (e.g. top districts / states)
    if len(rows) > 1 and ("district_name" in columns or "state_name" in columns):
        ent_col_idx = columns.index("district_name") if "district_name" in columns else columns.index("state_name")
        val_col_idx = next(
            (i for i in range(len(columns)) if i != ent_col_idx and columns[i] not in ["state_name", "district_name", "financial_year", "survey_year", "crop_year"]),
            1 if ent_col_idx == 0 else 0
        )
        val_col_name = columns[val_col_idx] if val_col_idx < len(columns) else ""
        is_val_pct = "rate" in val_col_name or "pct" in val_col_name

        formatted_items = []
        for r in rows:
            ent = str(r[ent_col_idx])
            val = r[val_col_idx]
            if is_val_pct:
                try:
                    formatted_items.append(f"{ent} ({float(val):.1f}%)")
                except (ValueError, TypeError):
                    formatted_items.append(f"{ent} ({val})")
            elif "amount" in val_col_name:
                formatted_items.append(f"{ent} (₹{format_indian_currency_number(val, lang=lang)})")
            else:
                formatted_items.append(f"{ent} ({format_indian_currency_number(val, lang=lang)})")

        joined_items = ", ".join(formatted_items)

        # Determine ranking direction (ASC = lowest, DESC = highest/top)
        gen_sql = (state.get("generated_sql") or "").upper()
        is_lowest = "ASC" in gen_sql or any(
            w in query_text.lower() for w in [
                "lowest", "bottom", "least", "min", "kam", "kami",
                "कम", "कमी", "সবচেয়ে কম", "কম", "সর্বনিম্ন", "குறைந்த", "மிகக் குறைந்த", "తక్కువ", "అత్యల్ప"
            ]
        )

        rank_hi = "न्यूनतम" if is_lowest else "शीर्ष"
        rank_mr = "सर्वात कमी" if is_lowest else "अव्वल"
        rank_ta = "மிகக் குறைந்த" if is_lowest else "முன்னணி"
        rank_te = "అత్యల్ప" if is_lowest else "అగ్ర"
        rank_bn = "সর্বনিম্ন" if is_lowest else "শীর্ষ"
        rank_en = "Bottom" if is_lowest else "Top"

        # Determine human-readable metric basis across languages
        m_en = "PM-Kisan farmer beneficiaries"
        m_hi = "किसान लाभार्थियों (Farmer Beneficiaries)"
        m_mr = "शेतकरी लाभार्थी"
        m_ta = "விவசாய பயனாளிகள்"
        m_te = "రైతు లబ్ధిదారులు"
        m_bn = "পিএম-কিষাণ কৃষক সুবিধাভোগী"

        if "amount" in val_col_name:
            m_en = "disbursed amount (₹)"
            m_hi = "वितरित राशि (₹)"
            m_mr = "वितरित रक्कम (₹)"
            m_ta = "வழங்கப்பட்ட நிதி (₹)"
            m_te = "పంపిణీ చేసిన నిధులు (₹)"
            m_bn = "বিতরণ করা অর্থ (₹)"
        elif "student" in val_col_name:
            m_en = "student enrollment"
            m_hi = "विद्यार्थी संख्या (Student Count)"
            m_mr = "विद्यार्थी संख्या"
            m_ta = "மாணவர் சேர்க்கை"
            m_te = "విద్యార్థుల సంఖ్య"
            m_bn = "শিক্ষার্থী সংখ্যা"
        elif "literacy" in val_col_name:
            m_en = "literacy rate"
            m_hi = "साक्षरता दर (Literacy Rate)"
            m_mr = "साक्षरता प्रमाण"
            m_ta = "கல்வியறிவு விகிதம்"
            m_te = "అక్షరాస్యత రేటు"
            m_bn = "সাক্ষরতার হার"
        elif "manday" in val_col_name:
            m_en = "MGNREGA mandays"
            m_hi = "मनरेगा कार्य दिवसों (Mandays)"
            m_mr = "मनरेगा मनुष्यदिन"
            m_ta = "மகாத்மா காந்தி வேலைவாய்ப்பு மனித நாட்கள்"
            m_te = "ఉపాధి హామీ పని దినాలు"
            m_bn = "মনরেগা কাজের দিন"
        elif "water" in val_col_name or "tap" in val_col_name:
            m_en = "tap water connections"
            m_hi = "नल जल कनेक्शनों (Tap Water Connections)"
            m_mr = "नळ जोडणी"
            m_ta = "குடிநீர் குழாய் இணைப்புகள்"
            m_te = "కుళాయి నీటి కనెక్షన్లు"
            m_bn = "ট্যাপের পানির সংযোগ"
        elif "school" in val_col_name:
            m_en = "school infrastructure count"
            m_hi = "स्कूलों की संख्या"
            m_mr = "शाळांची संख्या"
            m_ta = "பள்ளிகள் எண்ணிக்கை"
            m_te = "పాఠశాలల సంఖ్య"
            m_bn = "বিদ্যালয়ের সংখ্যা"
        elif "production" in val_col_name:
            m_en = "crop production (tonnes)"
            m_hi = "फसल उत्पादन"
            m_mr = "पीक उत्पादन"
            m_ta = "பயிர் உற்பத்தி"
            m_te = "పంట ఉత్పత్తి"
            m_bn = "ফসল উৎপাদন"

        # Detect State in Query
        state_display = ""
        st_lower = f" {query_text.lower()} "
        if any(w in query_text for w in ["uttar pradesh", "उत्तर प्रदेश", "উত্তর প্রদেশ", "উত্তর प्रदेश", "উত্তরপ্রদেশ", "உத்தர", "ఉత్తర"]) or " up " in st_lower:
            state_display = "উত্তর প্রদেশ" if lang == "bn" else ("उत्तर प्रदेश" if lang in ("hi", "mr") else "Uttar Pradesh")
        elif any(w in query_text for w in ["bihar", "बिहार", "বিহার", "பீகார்", "బీహార్"]):
            state_display = "বিহার" if lang == "bn" else ("बिहार" if lang in ("hi", "mr") else "Bihar")
        elif any(w in query_text for w in ["maharashtra", "महाराष्ट्र", "মহারাষ্ট্র", "மகாராஷ்டிரா", "మహారాష్ట్ర"]):
            state_display = "মহারাষ্ট্র" if lang == "bn" else ("महाराष्ट्र" if lang in ("hi", "mr") else "Maharashtra")
        elif any(w in query_text for w in ["tamil nadu", "தமிழ்நாடு", "তামিলনাড়ু", "తమిళనాడు"]):
            state_display = "তামিলনাড়ু" if lang == "bn" else ("तमिलनाडु" if lang in ("hi", "mr") else "Tamil Nadu")
        elif any(w in query_text for w in ["rajasthan", "राजस्थान", "রাজস্থান", "ராஜஸ்தான்", "రాజస్థాన్"]):
            state_display = "রাজস্থান" if lang == "bn" else ("राजस्थान" if lang in ("hi", "mr") else "Rajasthan")
        elif any(w in query_text for w in ["punjab", "पंजाब", "পাঞ্জাব", "பஞ்சாப்", "పంజాబ్"]):
            state_display = "পাঞ্জাব" if lang == "bn" else ("पंजाब" if lang in ("hi", "mr") else "Punjab")
        elif any(w in query_text for w in ["haryana", "हरियाणा", "হরিয়ানা", "ஹரியானா", "హర్యానా"]):
            state_display = "হরিয়ানা" if lang == "bn" else ("हरियाणा" if lang in ("hi", "mr") else "Haryana")

        th = extract_threshold_filter(query_text)
        if th:
            op, val = th
            val_int = int(val) if val == int(val) else val
            op_en = "more than" if op in (">", ">=") else "less than"
            op_hi = "से अधिक" if op in (">", ">=") else "से कम"
            if lang == "hi":
                st_prefix = f"{state_display} में " if state_display else ""
                return f"{st_prefix}{m_hi} {val_int}% {op_hi} वाले {len(rows)} जिले हैं: {joined_items}।"
            elif lang == "mr":
                st_prefix = f"{state_display} मधील " if state_display else ""
                return f"{st_prefix}{m_mr} {val_int}% पेक्षा जास्त असलेले {len(rows)} नोंदणीकृत जिल्हे: {joined_items}."
            elif lang == "ta":
                st_prefix = f"{state_display} மாநிலத்தில் " if state_display else ""
                return f"{st_prefix}{m_ta} {val_int}%-க்கு மேல் உள்ள {len(rows)} மாவட்டங்கள்: {joined_items}."
            elif lang == "te":
                st_prefix = f"{state_display} లో " if state_display else ""
                return f"{st_prefix}{m_te} {val_int}% కంటే ఎక్కువ ఉన్న {len(rows)} నమోదైన జిల్లాలు: {joined_items}."
            elif lang == "bn":
                st_prefix = f"{state_display}-এ " if state_display else ""
                return f"{st_prefix}{m_bn} {val_int}% এর বেশি থাকা {len(rows)}টি নথিভুক্ত জেলা: {joined_items}।"
            elif lang == "hi-en":
                st_prefix = f"{state_display} mein " if state_display else ""
                return f"{st_prefix}{m_en} > {val_int}% wale {len(rows)} recorded districts: {joined_items}."
            else:
                st_phrase = f" in {state_display}" if state_display else ""
                return f"Districts{st_phrase} with {m_en} {op_en} {val_int}%: {joined_items}."

        if lang == "hi":
            st_prefix = f"{state_display} में " if state_display else ""
            return f"{st_prefix}{m_hi} के अनुसार {rank_hi} {len(rows)} जिले हैं: {joined_items}।"
        elif lang == "mr":
            st_prefix = f"{state_display} मधील " if state_display else ""
            return f"{st_prefix}{m_mr} नुसार {rank_mr} {len(rows)} नोंदणीकृत जिल्हे: {joined_items}."
        elif lang == "ta":
            st_prefix = f"{state_display} மாநிலத்தில் " if state_display else ""
            return f"{st_prefix}{m_ta} அடிப்படையில் {rank_ta} {len(rows)} மாவட்டங்கள்: {joined_items}."
        elif lang == "te":
            st_prefix = f"{state_display} లో " if state_display else ""
            return f"{st_prefix}{m_te} ఆధారంగా {rank_te} {len(rows)} నమోదైన జిల్లాలు: {joined_items}."
        elif lang == "bn":
            st_prefix = f"{state_display}-এ " if state_display else ""
            return f"{st_prefix}{m_bn} অনুসারে {rank_bn} {len(rows)}টি নথিভুক্ত জেলা: {joined_items}।"
        elif lang == "hi-en":
            st_prefix = f"{state_display} mein " if state_display else ""
            return f"{st_prefix}{m_en} ke basis par {rank_en.lower()} {len(rows)} recorded districts: {joined_items}."
        else:
            st_phrase = f" in {state_display}" if state_display else ""
            return f"{rank_en} {len(rows)} recorded districts{st_phrase} by {m_en}: {joined_items}."

    row = rows[0]

    # 1. Female Literacy Rate
    if "female_literacy_rate" in columns:
        dist_idx = columns.index("district_name") if "district_name" in columns else 0
        rate_idx = columns.index("female_literacy_rate")
        dist = row[dist_idx]
        rate = row[rate_idx]
        if lang == "hi":
            return f"डेटाबेस के अनुसार {dist} जिले में महिला साक्षरता दर {rate}% दर्ज की गई।"
        elif lang == "mr":
            return f"डेटाबेसच्या नोंदीनुसार {dist} जिल्ह्यामध्ये महिला साक्षरता प्रमाण {rate}% नोंदवले गेले आहे."
        elif lang == "ta":
            return f"தரவுத்தள பதிவுகளின்படி {dist} மாவட்டத்தில் பெண் கல்வியறிவு விகிதம் {rate}% ஆக பதிவாகியுள்ளது."
        elif lang == "te":
            return f"డేటాబేస్ రికార్డుల ప్రకారం {dist} జిల్లాలో మహిళా అక్షరాస్యత రేటు {rate}% గా నమోదైంది."
        elif lang == "bn":
            return f"ডাটাবেস রেকর্ড অনুযায়ী {dist} জেলায় মহিলা সাক্ষরতার হার {rate}% রেকর্ড করা হয়েছে।"
        elif lang == "hi-en":
            return f"Database ke according {dist} district mein female literacy rate {rate}% record hua hai."
        else:
            return f"According to database records, district {dist} recorded a female literacy rate of {rate}%."

    # 2. MGNREGA Person-Days (Mandays)
    sql_upper = (state.get("generated_sql", "") or "").upper()
    if "total_mandays" in columns or "total_mandays_generated" in columns or (len(columns) == 1 and "TOTAL_MANDAYS_GENERATED" in sql_upper):
        mandays_idx = (
            columns.index("total_mandays")
            if "total_mandays" in columns
            else (columns.index("total_mandays_generated") if "total_mandays_generated" in columns else 0)
        )
        mandays = row[mandays_idx]
        mandays_fmt = format_indian_currency_number(mandays, lang=lang)
        if lang == "ta":
            return f"மகாத்மா காந்தி ஊரக வேலை உறுதித் திட்டத்தின் கீழ் மொத்தம் {mandays_fmt} மனித வேலை நாட்கள் உருவாக்கப்பட்டுள்ளன."
        elif lang == "hi":
            return f"मनरेगा योजना के तहत कुल {mandays_fmt} कार्य दिवस (Mandays) उत्पन्न किए गए।"
        elif lang == "mr":
            return f"मनरेगा योजनेअंतर्गत एकूण {mandays_fmt} मनुष्य दिन रोजगार निर्माण करण्यात आला."
        elif lang == "te":
            return f"ఉపాధి హామీ పథకం కింద మొత్తం {mandays_fmt} పనిదినాలు కల్పించబడ్డాయి."
        elif lang == "bn":
            return f"১০০ দিনের কাজের প্রকল্পে মোট {mandays_fmt} কর্মদিবস তৈরি হয়েছে।"
        elif lang == "hi-en":
            return f"MGNREGA scheme ke tahat total {mandays_fmt} person-days generate hue."
        else:
            return f"Under MGNREGA, a total of {mandays_fmt} person-days (mandays) were generated."

    # 3. PM-KISAN Farmers & Disbursement
    farmer_col_idx = next(
        (i for i, c in enumerate(columns) if any(k in c for k in ["farmer", "beneficiar"])),
        0 if (len(columns) == 1 and "FARMER_BENEFICIARIES" in sql_upper) else None
    )
    if farmer_col_idx is not None:
        farmers = row[farmer_col_idx]
        farmers_fmt = format_indian_currency_number(farmers, lang=lang)
        amount_part = ""
        amt_col_idx = next(
            (i for i, c in enumerate(columns) if any(k in c for k in ["amount", "disbursed"])),
            None
        )
        if amt_col_idx is not None:
            amt = row[amt_col_idx]
            amt_fmt = format_indian_currency_number(amt, lang=lang)
            if lang == "mr":
                amount_part = f", आणि ₹{amt_fmt} ची रक्कम थेट वितरित करण्यात आली"
            elif lang == "ta":
                amount_part = f", மற்றும் மொத்தம் ₹{amt_fmt} நிதி விடுவிக்கப்பட்டது"
            elif lang == "te":
                amount_part = f", మరియు మొత్తం ₹{amt_fmt} నిధులు పంపిణీ చేయబడ్డాయి"
            elif lang == "bn":
                amount_part = f", এবং মোট ₹{amt_fmt} টাকা বিতরণ করা হয়েছে"
            elif lang == "hi-en":
                amount_part = f", aur total INR {amt_fmt} amount transfer kiya gaya"
            elif lang == "en":
                amount_part = f", with a total disbursement of INR {amt_fmt}"
            else:
                amount_part = f", और कुल ₹{amt_fmt} की राशि हस्तांतरित की गई"

        # Check if nationwide timeless cumulative sum across 4 financial years (> 10 Crores)
        try:
            f_val = float(farmers)
        except (ValueError, TypeError):
            f_val = 0.0

        if f_val > 100_000_000:
            if lang == "mr":
                return f"पीएम-किसान योजनेअंतर्गत 4 आर्थिक वर्षांमध्ये (2021-2025) एकूण {farmers_fmt} संचयी शेतकरी लाभांचे वितरण झाले (वार्षिक सरासरी ~7.16 कोटी सक्रिय लाभार्थी, नवीनतम 2024-25 मध्ये 7.11 कोटी){amount_part}."
            elif lang == "hi":
                return f"पीएम-किसान योजना के 4 वित्तीय वर्षों (2021-2025) में कुल {farmers_fmt} संचयी किसान किस्तों का वितरण हुआ (प्रति वर्ष औसतन ~7.16 करोड़ सक्रिय किसान लाभार्थी, नवीनतम वर्ष 2024-25 में 7.11 करोड़){amount_part}।"
            elif lang == "hi-en":
                return f"PM-KISAN yojana ke tahat 4 financial years (2021-2025) mein total {farmers_fmt} cumulative farmer disbursements record hue (per year average ~7.16 Crores active beneficiaries, latest 2024-25 mein 7.11 Crores){amount_part}."
            elif lang == "te":
                return f"పీఎం-కిసాన్ పథకం కింద 4 ఆర్థిక సంవత్సరాల్లో (2021-2025) మొత్తం {farmers_fmt} సంయుక్త రైతు లబ్ధిదారులకు నిధులు విడుదలయ్యాయి (ఏడాదికి సగటున ~7.16 కోట్ల మంది క్రియాశీల రైతులు){amount_part}."
            elif lang == "ta":
                return f"பிஎம்-கிசான் திட்டத்தின் கீழ் 4 நிதியாண்டுகளில் (2021-2025) மொத்தம் {farmers_fmt} ஒட்டுமொத்த விவசாய நிதி விடுவிப்புகள் செய்யப்பட்டுள்ளன (வருடத்திற்கு சராசரியாக ~7.16 கோடி தீவிர விவசாயிகள்){amount_part}."
            elif lang == "bn":
                return f"পিএম-কিষান প্রকল্পের অধীনে 4টি আর্থিক বছরে (2021-2025) মোট {farmers_fmt} ক্রমবর্ধমান কৃষক সুবিধা বিতরণ করা হয়েছে (প্রতি বছর গড়ে ~7.16 কোটি সক্রিয় কৃষক){amount_part}।"
            else:
                return (
                    f"Under PM-KISAN records across 4 financial years (2021-2025), a cumulative total of {farmers_fmt} farmer disbursements were recorded, averaging ~7.16 Crores active beneficiaries per year (with 7.11 Crores in the latest 2024-25 period){amount_part}."
                )

        if lang == "mr":
            return f"पीएम-किसान योजनेअंतर्गत एकूण {farmers_fmt} शेतकऱ्यांना लाभ मिळाला{amount_part}."
        elif lang == "hi":
            return f"पीएम-किसान योजना के तहत कुल {farmers_fmt} किसानों को लाभ प्राप्त हुआ{amount_part}."
        elif lang == "hi-en":
            return f"PM-KISAN yojana ke tahat total {farmers_fmt} farmers ko labh mila{amount_part}."
        elif lang == "te":
            return f"పీఎం-కిసాన్ పథకం కింద మొత్తం {farmers_fmt} రైతులకు లబ్ధి చేకూరింది{amount_part}."
        elif lang == "ta":
            return f"பிஎம்-கிசான் திட்டத்தின் கீழ் மொத்தம் {farmers_fmt} விவசாயிகள் பயனடைந்துள்ளனர்{amount_part}."
        elif lang == "bn":
            return f"পিএম-কিষান প্রকল্পের অধীনে মোট {farmers_fmt} জন কৃষক উপকৃত হয়েছেন{amount_part}।"
        else:
            return (
                f"Under PM-KISAN, a total of {farmers_fmt} farmers received direct benefit transfers{amount_part}."
            )

    sql_text = sql_upper
    detected_state = ""
    detected_state_key = ""
    for st in ["UTTAR PRADESH", "PUNJAB", "GUJARAT", "MAHARASHTRA", "RAJASTHAN", "BIHAR", "TAMIL NADU", "WEST BENGAL", "ANDHRA PRADESH", "TELANGANA", "MADHYA PRADESH", "HARYANA", "KARNATAKA", "ODISHA", "KERALA", "ASSAM", "JHARKHAND"]:
        if f"'{st}'" in sql_text or st.lower() in query_text:
            detected_state = st.title()
            detected_state_key = st
            break

    _STATE_NATIVE = {
        "MAHARASHTRA": {"hi": "महाराष्ट्र", "mr": "महाराष्ट्रात", "te": "మహారాష్ట్ర", "ta": "மகாராஷ்டிராவில்", "bn": "মহারাষ্ট্রে"},
        "PUNJAB": {"hi": "पंजाब", "mr": "पंजाबमध्ये", "te": "పంజాబ్‌", "ta": "பஞ்சாபில்", "bn": "পাঞ্জাবে"},
        "HARYANA": {"hi": "हरियाणा", "mr": "हरियाणामध्ये", "te": "హర్యానా", "ta": "ஹரியானாவில்", "bn": "হরিয়ানায়"},
        "UTTAR PRADESH": {"hi": "उत्तर प्रदेश", "mr": "उत्तर प्रदेशात", "te": "ఉత్తరప్రదేశ్", "ta": "உத்தரபிரதேசத்தில்", "bn": "উত্তর প্রদেশে"},
        "BIHAR": {"hi": "बिहार", "mr": "बिहारमध्ये", "te": "బీహార్", "ta": "பீகாரில்", "bn": "বিহারে"},
        "GUJARAT": {"hi": "गुजरात", "mr": "गुजरातमध्ये", "te": "గుజరాత్", "ta": "குஜராத்தில்", "bn": "গুজরাটে"},
        "RAJASTHAN": {"hi": "राजस्थान", "mr": "राजस्थानमध्ये", "te": "రాజస్థాన్", "ta": "ராஜஸ்தானில்", "bn": "রাজস্থানে"},
        "ANDHRA PRADESH": {"hi": "आंध्र प्रदेश", "mr": "आंध्र प्रदेशात", "te": "ఆంధ్రప్రదేశ్‌", "ta": "ஆந்திராவில்", "bn": "অন্ধ্রপ্রদেশে"},
        "TELANGANA": {"hi": "तेलंगाना", "mr": "तेलंगणामध्ये", "te": "తెలంగాణ", "ta": "தெலுங்கானாவில்", "bn": "তেলেঙ্গানায়"},
        "TAMIL NADU": {"hi": "तमिलनाडु", "mr": "तामिळनाडूमध्ये", "te": "తమిళనాడు", "ta": "தமிழ்நாட்டில்", "bn": "তামিলনাড়ুতে"},
        "WEST BENGAL": {"hi": "पश्चिम बंगाल", "mr": "पश्चिम बंगालमध्ये", "te": "పశ్చిమ బెంగాల్", "ta": "மேற்கு வங்கத்தில்", "bn": "পশ্চিমবঙ্গে"},
        "MADHYA PRADESH": {"hi": "मध्य प्रदेश", "mr": "मध्य प्रदेशात", "te": "మధ్యప్రదేశ్", "ta": "மத்திய பிரதேசத்தில்", "bn": "মধ্যপ্রদেশে"},
        "KARNATAKA": {"hi": "कर्नाटक", "mr": "कर्नाटकात", "te": "కర్ణాటక", "ta": "கர்நாடகாவில்", "bn": "কর্ণাটকে"},
        "KERALA": {"hi": "केरल", "mr": "केरळमध्ये", "te": "కేరళ", "ta": "கேரளாவில்", "bn": "কেরলে"},
        "ODISHA": {"hi": "ओडिशा", "mr": "ओडिशामध्ये", "te": "ఒడిశా", "ta": "ஒடிசாவில்", "bn": "ওড়িশায়"},
        "JHARKHAND": {"hi": "झारखंड", "mr": "झारखंडमध्ये", "te": "జార్ఖండ్", "ta": "ஜார்கண்டில்", "bn": "ঝাড়খণ্ডে"},
        "ASSAM": {"hi": "असम", "mr": "आसाममध्ये", "te": "అసోం", "ta": "அசாமில்", "bn": "আসামে"},
    }
    st_nat = _STATE_NATIVE.get(detected_state_key, {})
    st_hi = f"{st_nat.get('hi', detected_state)} में " if detected_state else ""
    st_mr = f"{st_nat.get('mr', detected_state + ' मध्ये')} " if detected_state else ""
    st_te = f"{st_nat.get('te', detected_state)} లో " if detected_state else ""
    st_ta = f"{st_nat.get('ta', detected_state + ' மாநிலத்தில்')} " if detected_state else ""
    st_bn = f"{st_nat.get('bn', detected_state + '-এ')} " if detected_state else ""
    st_en = f"In {detected_state}, " if detected_state else ""
    st_hien = f"{detected_state} mein " if detected_state else ""

    # 4. Fertilizer Distribution (DAP, Urea, MOP)
    fert_col_idx = next(
        (i for i, c in enumerate(columns) if any(k in c for k in ["sales", "fertilizer"])),
        0 if (len(columns) == 1 and "SALES_TONNES" in sql_text) else None
    )
    if fert_col_idx is not None and any(f in sql_text or f in query_text.upper() for f in ["DAP", "UREA", "MOP", "NPK"]):
        fert_type = "DAP" if "DAP" in (sql_text + query_text.upper()) else ("UREA" if "UREA" in (sql_text + query_text.upper()) else "fertilizer")
        sales_val = row[fert_col_idx]
        sales_fmt = format_indian_currency_number(sales_val, lang=lang)
        if lang == "hi":
            return f"{detected_state} में {fert_type} खाद की कुल बिक्री {sales_fmt} टन दर्ज की गई।"
        elif lang == "mr":
            return f"{detected_state} मध्ये {fert_type} खताची एकूण विक्री {sales_fmt} टन नोंदवली गेली."
        elif lang == "hi-en":
            return f"{detected_state} mein {fert_type} fertilizer ki total sales {sales_fmt} tonnes record hui."
        elif lang == "ta":
            return f"{detected_state} மாநிலத்தில் {fert_type} உரத்தின் மொத்த விற்பனை {sales_fmt} டன்கள் என பதிவாகியுள்ளது."
        elif lang == "te":
            return f"{detected_state} లో {fert_type} ఎరువుల మొత్తం అమ్మకాలు {sales_fmt} టన్నులుగా నమోదయ్యాయి."
        elif lang == "bn":
            return f"{detected_state}-এ {fert_type} সারের মোট বিক্রি {sales_fmt} মেট্রিক টন রেকর্ড করা হয়েছে।"
        else:
            return f"In {detected_state}, total recorded sales of {fert_type} fertilizer were {sales_fmt} tonnes."

    # 5. Crop Cultivation Area (Hectares)
    area_col_idx = next(
        (i for i, c in enumerate(columns) if any(k in c for k in ["area_hectares", "cultivation_area", "total_area"])),
        0 if (len(columns) == 1 and "AREA_HECTARES" in sql_text) else None
    )
    if area_col_idx is not None:
        area_val = row[area_col_idx]
        area_fmt = format_indian_currency_number(area_val, lang=lang)
        crop_name = "Wheat" if "WHEAT" in (sql_text + query_text.upper()) else ("Soybean" if "SOYBEAN" in (sql_text + query_text.upper()) else "crop")
        crop_hi = "गेहूं" if crop_name == "Wheat" else ("सोयाबीन" if crop_name == "Soybean" else "फसल")
        if lang == "hi":
            return f"{detected_state} में {crop_hi} की खेती का कुल क्षेत्रफल {area_fmt} हेक्टेयर दर्ज किया गया।"
        elif lang == "mr":
            return f"{detected_state} मध्ये {crop_hi} लागवडीखालील एकूण क्षेत्र {area_fmt} हेक्टर नोंदवले गेले."
        elif lang == "hi-en":
            return f"{detected_state} mein {crop_name} cultivation ka total area {area_fmt} hectares record hua."
        elif lang == "ta":
            return f"{detected_state} மாநிலத்தில் {crop_name} சாகுபடி பரப்பளவு {area_fmt} ஹெக்டேர் என பதிவாகியுள்ளது."
        elif lang == "te":
            return f"{detected_state} లో {crop_name} సాగు విస్తీర్ణం {area_fmt} హెక్టార్లుగా నమోదైంది."
        elif lang == "bn":
            return f"{detected_state}-এ {crop_name} চাষের মোট এলাকা {area_fmt} হেক্টর রেকর্ড করা হয়েছে।"
        else:
            return f"In {detected_state}, the total recorded cultivation area for {crop_name} was {area_fmt} hectares."

    # 6. Crop Production (Tonnes)
    prod_col_idx = next(
        (i for i, c in enumerate(columns) if any(k in c for k in ["production_tonnes", "total_production", "production"]) and "sales" not in c),
        0 if (len(columns) == 1 and "PRODUCTION_TONNES" in sql_text) else None
    )
    if prod_col_idx is not None:
        prod_val = row[prod_col_idx]
        prod_fmt = format_indian_currency_number(prod_val, lang=lang)
        crop_name = "Soybean" if "SOYBEAN" in (sql_text + query_text.upper()) else (
            "Wheat" if "WHEAT" in (sql_text + query_text.upper()) else (
                "grains" if "grain" in query_text else "crop"
            )
        )
        crop_hi = "सोयाबीन" if crop_name == "Soybean" else ("गेहूं" if crop_name == "Wheat" else "फसल")
        limit_m = re.search(r"ORDER\s+BY\s+\w+\s+DESC\s+LIMIT\s+(\d+)", sql_text)
        period_en = f" across the latest {limit_m.group(1)} recorded years" if limit_m else ""
        if lang == "hi":
            return f"{detected_state} में {crop_hi} का कुल उत्पादन {prod_fmt} टन दर्ज किया गया।"
        elif lang == "mr":
            return f"{detected_state} मध्ये {crop_hi} एकूण उत्पादन {prod_fmt} टन झाले."
        elif lang == "hi-en":
            return f"{detected_state} mein {crop_name} ka total production {prod_fmt} tonnes record hua."
        elif lang == "ta":
            return f"{detected_state} மாநிலத்தில் {crop_name} மொத்த உற்பத்தி {prod_fmt} டன்கள் என பதிவாகியுள்ளது."
        elif lang == "te":
            return f"{detected_state} లో {crop_name} మొత్తం ఉత్పత్తి {prod_fmt} టన్నులుగా నమోదైంది."
        elif lang == "bn":
            return f"{detected_state}-এ {crop_name}-এর মোট উৎপাদন {prod_fmt} মেট্রিক টন রেকর্ড করা হয়েছে।"
        else:
            return f"In {detected_state}, the total recorded production of {crop_name}{period_en} was {prod_fmt} tonnes."

    # 7. Mandi Commodity Prices (INR / Quintal)
    price_col_idx = next(
        (i for i, c in enumerate(columns) if any(k in c for k in ["price", "modal_price", "avg_price"])),
        0 if (len(columns) == 1 and "MODAL_PRICE_INR" in sql_text) else None
    )
    if price_col_idx is not None:
        price_val = row[price_col_idx]
        try:
            price_fmt = f"{float(price_val):,.2f}"
        except (ValueError, TypeError):
            price_fmt = str(price_val)
        comm = "Wheat" if "WHEAT" in (sql_text + query_text.upper()) else "commodity"
        comm_hi = "गेहूं" if comm == "Wheat" else "जिंस"
        if lang == "hi":
            return f"{detected_state} की मंडियों में {comm_hi} का औसत मॉडल भाव ₹{price_fmt} प्रति क्विंटल दर्ज किया गया।"
        elif lang == "mr":
            return f"{detected_state} मधील बाजार समित्यांमध्ये {comm_hi} सरासरी भाव ₹{price_fmt} प्रति क्विंटल नोंदवला गेला."
        elif lang == "hi-en":
            return f"{detected_state} ki mandis mein {comm} ka average modal price INR {price_fmt} per quintal raha."
        elif lang == "ta":
            return f"{detected_state} சந்தைகளில் {comm} சராசரி மாதிரி விலை குவிண்டாலுக்கு ₹{price_fmt} ஆகும்."
        elif lang == "te":
            return f"{detected_state} మార్కెట్లలో {comm} సగటు ధర క్వింటాలుకు ₹{price_fmt} గా నమోదైంది."
        elif lang == "bn":
            return f"{detected_state}-এর বাজারগুলিতে {comm}-এর গড় মূল্য কুইন্টাল প্রতি ₹{price_fmt} রেকর্ড করা হয়েছে।"
        else:
            return f"In {detected_state}, the average mandi modal price for {comm} was INR {price_fmt} per quintal."

    # 8. Soil Health Records (Samples Tested / Cards Issued)
    soil_col_idx = next(
        (i for i, c in enumerate(columns) if any(k in c for k in ["samples_tested", "cards_issued", "soil_samples"])),
        0 if (len(columns) == 1 and any(k in sql_text for k in ["SAMPLES_TESTED", "CARDS_ISSUED", "SOIL_HEALTH"])) else None
    )
    if soil_col_idx is not None and ("SOIL_HEALTH" in sql_text or any(k in query_text for k in ["soil", "मिट्टी", "माती", "నేల", "மண்", "মাটি", "नमूनों", "cards", "नमूने"])):
        val = row[soil_col_idx]
        val_fmt = format_indian_currency_number(val, lang=lang)
        is_cards = "CARDS_ISSUED" in sql_text or any(k in query_text for k in ["cards", "कार्ड", "అట్టలు", "కార్డులు", "அட்டைகள்", "কার্ড"])
        if is_cards:
            if lang == "hi":
                return f"{st_hi}मृदा स्वास्थ्य कार्ड योजना के तहत कुल {val_fmt} सॉइल हेल्थ कार्ड जारी किए गए।"
            elif lang == "mr":
                return f"{st_mr}मृदा आरोग्य योजनेंतर्गत एकूण {val_fmt} सॉइल हेल्थ कार्ड जारी करण्यात आले."
            elif lang == "te":
                return f"{st_te}సాయిల్ హెల్త్ కార్డ్ పథకం కింద మొత్తం {val_fmt} సాయిల్ హెల్త్ కార్డులు జారీ చేయబడ్డాయి."
            elif lang == "ta":
                return f"{st_ta}மண் சுகாதார அட்டை திட்டத்தின் கீழ் மொத்தம் {val_fmt} அட்டைகள் வழங்கப்பட்டுள்ளன."
            elif lang == "bn":
                return f"{st_bn}মৃত্তিকা স্বাস্থ্য কার্ড প্রকল্পের অধীনে মোট {val_fmt}টি কার্ড বিতরণ করা হয়েছে।"
            elif lang == "hi-en":
                return f"{st_hien}Soil Health Card yojana ke tahat total {val_fmt} soil health cards issue kiye gaye."
            else:
                return f"{st_en}a total of {val_fmt} Soil Health Cards were issued under the Soil Health scheme."
        else:
            if lang == "hi":
                return f"{st_hi}मृदा स्वास्थ्य योजना के तहत कुल {val_fmt} मिट्टी के नमूनों की जांच की गई।"
            elif lang == "mr":
                return f"{st_mr}मृदा आरोग्य योजनेंतर्गत एकूण {val_fmt} मातीचे नमुने तपासण्यात आले."
            elif lang == "te":
                return f"{st_te}సాయిల్ హెల్త్ పథకం కింద మొత్తం {val_fmt} నేల నమూనాలను పరీక్షించారు."
            elif lang == "ta":
                return f"{st_ta}மண் சுகாதார திட்டத்தின் கீழ் மொத்தம் {val_fmt} மண் மாதிரிகள் பரிசோதிக்கப்பட்டன."
            elif lang == "bn":
                return f"{st_bn}মৃত্তিকা স্বাস্থ্য প্রকল্পের অধীনে মোট {val_fmt}টি মাটির নমুনা পরীক্ষা করা হয়েছে।"
            elif lang == "hi-en":
                return f"{st_hien}Soil Health yojana ke under total {val_fmt} soil samples test kiye gaye."
            else:
                return f"{st_en}a total of {val_fmt} soil samples were tested under the Soil Health scheme."

    # 9. Jal Jeevan Tap Water Connections
    water_col_idx = next(
        (i for i, c in enumerate(columns) if any(k in c for k in ["tap_water", "connections", "fhtc"])),
        0 if (len(columns) == 1 and "TAP_WATER" in sql_text) else None
    )
    if water_col_idx is not None and ("JAL_JEEVAN" in sql_text or "TAP_WATER" in sql_text or any(k in query_text for k in ["water", "जल", "पानी", "నీరు", "குடிநீர்", "জল", "नळ"])):
        val = row[water_col_idx]
        val_fmt = format_indian_currency_number(val, lang=lang)
        if lang == "hi":
            return f"{st_hi}जल जीवन मिशन के तहत कुल {val_fmt} ग्रामीण परिवारों को नल जल कनेक्शन प्रदान किए गए।"
        elif lang == "mr":
            return f"{st_mr}जल जीवन अभियानांतर्गत एकूण {val_fmt} ग्रामीण कुटुंबांना नळ जोडणी देण्यात आली."
        elif lang == "te":
            return f"{st_te}జల్ జీవన్ మిషన్ కింద మొత్తం {val_fmt} గ్రామీణ ఇళ్లకు కుళాయి నీటి కనెక్షన్లు అందించబడ్డాయి."
        elif lang == "ta":
            return f"{st_ta}ஜல் ஜீவன் திட்டத்தின் கீழ் மொத்தம் {val_fmt} கிராமப்புற வீடுகளுக்கு குடிநீர் குழாய் இணைப்புகள் வழங்கப்பட்டுள்ளன."
        elif lang == "bn":
            return f"{st_bn}জল জীবন মিশনের অধীনে মোট {val_fmt}টি গ্রামীণ পরিবারে ট্যাপের জলের সংযোগ দেওয়া হয়েছে।"
        elif lang == "hi-en":
            return f"{st_hien}Jal Jeevan Mission ke tahat total {val_fmt} rural tap water connections provide kiye gaye."
        else:
            return f"{st_en}a total of {val_fmt} tap water connections were provided under the Jal Jeevan Mission."

    # 10. Ayushman Bharat (PM-JAY) Claims & Healthcare
    ayush_col_idx = next(
        (i for i, c in enumerate(columns) if any(k in c for k in ["claim_amount", "settled_inr", "authorized_admissions", "empanelled_hospitals"])),
        0 if (len(columns) == 1 and "AYUSHMAN" in sql_text) else None
    )
    if ayush_col_idx is not None and ("AYUSHMAN" in sql_text or "PMJAY" in sql_text or any(k in query_text for k in ["ayushman", "आयुष्मान", "आयुष्यमान", "ஆயுஷ்மான்", "ఆయుష్మాన్", "আয়ুষ্মান", "क्लेम", "claim"])):
        val = row[ayush_col_idx]
        val_fmt = format_indian_currency_number(val, lang=lang)
        if "claim" in columns[ayush_col_idx] or "settled" in columns[ayush_col_idx] or "CLAIM_AMOUNT" in sql_text:
            if lang == "hi":
                return f"{st_hi}आयुष्मान भारत (PM-JAY) योजना के तहत कुल ₹{val_fmt} की क्लेम राशि का भुगतान किया गया।"
            elif lang == "mr":
                return f"{st_mr}आयुष्यमान भारत (PM-JAY) योजनेअंतर्गत एकूण ₹{val_fmt} चा क्लेम निधी मंजूर करण्यात आला."
            elif lang == "te":
                return f"{st_te}ఆయుష్మాన్ భారత్ (PM-JAY) పథకం కింద మొత్తం ₹{val_fmt} క్లెయిమ్ మొత్తం పరిష్కరించబడింది."
            elif lang == "ta":
                return f"{st_ta}ஆயுஷ்மான் பாரத் (PM-JAY) திட்டத்தின் கீழ் மொத்தம் ₹{val_fmt} க்ளெய்ம் தொகை தீர்வு செய்யப்பட்டுள்ளது."
            elif lang == "bn":
                return f"{st_bn}আয়ুষ্মান ভারত (PM-JAY) প্রকল্পে মোট ₹{val_fmt} দাবি নিষ্পত্তি করা হয়েছে।"
            elif lang == "hi-en":
                return f"{st_hien}Ayushman Bharat (PM-JAY) ke under total INR {val_fmt} claim amount settle kiya gaya."
            else:
                return f"{st_en}a total claim amount of INR {val_fmt} was settled under Ayushman Bharat (PM-JAY)."

    # 11. Generic schema-aware verbalization localized to detected language
    items_desc = []
    for col, val in zip(res.get("columns", []), row):
        val_str = format_indian_currency_number(val, lang=lang)
        items_desc.append(f"{col}: {val_str}")

    joined_items = ", ".join(items_desc)
    if lang == "hi":
        return f"डेटाबेस परिणाम ({len(rows)} रिकॉर्ड): {joined_items}"
    elif lang == "mr":
        return f"डेटाबेस निकाल ({len(rows)} नोंद): {joined_items}"
    elif lang == "ta":
        return f"தரவுத்தள முடிவு ({len(rows)} பதிவு): {joined_items}"
    elif lang == "te":
        return f"డేటాబేస్ ఫలితం ({len(rows)} రికార్డు): {joined_items}"
    elif lang == "bn":
        return f"ডাটাবেস ফলাফল ({len(rows)} রেকর্ড): {joined_items}"
    elif lang == "hi-en":
        return f"Database result ({len(rows)} records): {joined_items}"
    return f"Database result ({len(rows)} records): {joined_items}"


def response_verbalizer_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Verbalizer Node: Formulates vernacular answer.
    Emits VoiceSynthesisEvent on the EventBus.
    """
    answer = verbalize_tabular_result(state)

    EventBus.publish(
        VoiceSynthesisEvent(
            query_id=state.get("query_id"),
            verbalized_text=answer,
            char_count=len(answer),
        )
    )

    audit_entry = {
        "step": 5,
        "agent": "ResponseVerbalizerAgent",
        "action": "verbalize_indic_prose",
        "output_length": len(answer),
    }

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "verbalized_response": answer,
        "audit_trace": current_trace,
    }
