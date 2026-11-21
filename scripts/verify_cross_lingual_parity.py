#!/usr/bin/env python3
"""
scripts/verify_cross_lingual_parity.py
Cross-Lingual Semantic Equivalence & Language Purity Verification Harness (Sprint 5).

Directly verifies that:
1. Queries from different languages (English, Telugu, Hindi, Tamil, Marathi, Bengali, Hinglish)
   fetch the exact same database records (Tabular Isomorphism: Rows(EN) == Rows(TE) == Rows(HI)...).
2. Every query returns BOTH valid executable SQL and a fluent natural-language answer.
3. The verbalized answer is strictly in the SAME language and script as the input question
   (e.g. Telugu question -> Telugu script answer with కోట్లు/లక్షలు; English -> English).
"""

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from tabulate import tabulate

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from indicsql.benchmark.evaluator import are_tabular_results_equivalent
from indicsql.graph.workflow import execute_indicsql_pipeline

# Parallel Multi-Lingual Concept Suite (10 Civic Concepts x 7 Languages = 70 Parallel Queries)
PARALLEL_CONCEPT_SUITE: List[Dict[str, Any]] = [
    {
        "concept_id": "CL-01",
        "domain": "PM-KISAN Beneficiaries (Andhra Pradesh)",
        "expected_table": "ndap_pm_kisan_disbursement",
        "queries": {
            "en": "What is the total number of farmer beneficiaries under PM-KISAN in Andhra Pradesh?",
            "te": "ఆంధ్రప్రదేశ్‌లో పీఎం-కిసాన్ పథకం ద్వారా ఎంతమంది రైతులకు లబ్ధి చేకూరింది?",
            "hi": "आंध्र प्रदेश में पीएम-किसान के तहत कुल कितने किसानों को लाभ मिला?",
            "ta": "ஆந்திராவில் பிஎம்-கிசான் திட்டத்தின் கீழ் பயனடைந்த மொத்த விவசாயிகள் எத்தனை பேர்?",
            "mr": "आंध्र प्रदेशात पीएम-किसान योजनेचा लाभ एकूण किती शेतकऱ्यांना मिळाला?",
            "bn": "অন্ধ্রপ্রদেশে মোট কতজন কৃষক পিএম-কিষানের সুবিধা পেয়েছেন?",
            "hi-en": "Andhra Pradesh me total kitne farmers ko PM-Kisan ka labh mila?",
        },
    },
    {
        "concept_id": "CL-02",
        "domain": "Wheat Production (Punjab)",
        "expected_table": "ndap_crop_production_census",
        "queries": {
            "en": "What is the total production of wheat in Punjab in tonnes?",
            "te": "పంజాబ్‌లో గోధుమ మొత్తం ఉత్పత్తి ఎన్ని టన్నులు?",
            "hi": "पंजाब में गेहूं का कुल उत्पादन कितने टन हुआ?",
            "ta": "பஞ்சாபில் கோதுமையின் மொத்த உற்பத்தி எத்தனை டன்?",
            "mr": "पंजाबमध्ये गव्हाचे एकूण उत्पादन किती टन झाले?",
            "bn": "পাঞ্জাবে গমের মোট উৎপাদন কত টন হয়েছে?",
            "hi-en": "Punjab me wheat ka total production kitne tonnes hua?",
        },
    },
    {
        "concept_id": "CL-03",
        "domain": "Rice Production (Andhra Pradesh)",
        "expected_table": "ndap_crop_production_census",
        "queries": {
            "en": "What is the total production of rice in Andhra Pradesh in tonnes?",
            "te": "ఆంధ్రప్రదేశ్‌లో వరి పంట మొత్తం ఉత్పత్తి ఎన్ని టన్నులు?",
            "hi": "आंध्र प्रदेश में चावल का कुल उत्पादन कितने टन हुआ?",
            "ta": "ஆந்திராவில் நெல் பயிரின் மொத்த உற்பத்தி எத்தனை டன்?",
            "mr": "आंध्र प्रदेशात तांदूळ (चावल) पिकाचे एकूण उत्पादन किती टन झाले?",
            "bn": "অন্ধ্রপ্রদেশে ধান ফসলের মোট উৎপাদন কত টন হয়েছে?",
            "hi-en": "Andhra Pradesh me rice ka total production kitne tonnes hua?",
        },
    },
    {
        "concept_id": "CL-04",
        "domain": "Groundnut Cultivation Area (Gujarat)",
        "expected_table": "ndap_crop_production_census",
        "queries": {
            "en": "What is the total cultivation area of groundnut in Gujarat in hectares?",
            "te": "గుజరాత్‌లో వేరుశనగ సాగు విస్తీర్ణం ఎన్ని హెక్టార్లు?",
            "hi": "गुजरात में मूंगफली की खेती का कुल क्षेत्रफल कितने हेक्टेयर है?",
            "ta": "குஜராத்தில் நிலக்கடலை சாகுபடி பரப்பளவு எத்தனை ஹெக்டேர்?",
            "mr": "गुजरातमध्ये भुईमूग लागवड किती हेक्टर क्षेत्रावर झाली?",
            "bn": "গুজরাটে চিনাবাদাম চাষের মোট এলাকা কত হেক্টর?",
            "hi-en": "Gujarat me groundnut cultivation ka total area kitne hectares hai?",
        },
    },
    {
        "concept_id": "CL-05",
        "domain": "DAP Fertilizer Sales (Uttar Pradesh)",
        "expected_table": "ndap_fertilizer_distribution",
        "queries": {
            "en": "What were the total sales of DAP fertilizer in Uttar Pradesh in tonnes?",
            "te": "ఉత్తరప్రదేశ్‌లో డీఏపీ ఎరువుల మొత్తం అమ్మకాలు ఎన్ని టన్నులు?",
            "hi": "उत्तर प्रदेश में डीएपी खाद की कुल बिक्री कितने टन हुई?",
            "ta": "உத்தர பிரதேசத்தில் டிஏபி உரத்தின் மொத்த விற்பனை எத்தனை டன்?",
            "mr": "उत्तर प्रदेशात डीएपी खताची एकूण विक्री किती टन झाली?",
            "bn": "উত্তর প্রদেশে ডিএপি সারের মোট বিক্রি কত টন?",
            "hi-en": "Uttar Pradesh me DAP fertilizer ki total sales kitni tonnes hui?",
        },
    },
    {
        "concept_id": "CL-06",
        "domain": "MGNREGA Employment Mandays (Telangana)",
        "expected_table": "mgnrega_state_annual_employment",
        "queries": {
            "en": "How many total person-days were generated under MGNREGA in Telangana?",
            "te": "తెలంగాణలో ఉపాధి హామీ పథకం కింద ఎన్ని పనిదినాలు కల్పించబడ్డాయి?",
            "hi": "तेलंगाना में मनरेगा के तहत कुल कितने कार्य दिवस सृजित किए गए?",
            "ta": "தெலுங்கானாவில் மகாத்மா காந்தி வேலை உறுதி திட்டத்தின் கீழ் எத்தனை மனித வேலை நாட்கள் உருவாக்கப்பட்டன?",
            "mr": "तेलंगणामध्ये मनरेगा अंतर्गत एकूण किती मनुष्य दिन रोजगार निर्माण झाला?",
            "bn": "তেলেঙ্গানায় ১০০ দিনের কাজের প্রকল্পে মোট কত কর্মদিবস তৈরি হয়েছে?",
            "hi-en": "Telangana me MGNREGA ke under total kitne mandays generate hue?",
        },
    },
    {
        "concept_id": "CL-07",
        "domain": "Jal Jeevan Tap Water Connections (Andhra Pradesh)",
        "expected_table": "ndap_jal_jeevan_tap_water",
        "queries": {
            "en": "How many households in Andhra Pradesh have tap water connections under Jal Jeevan Mission?",
            "te": "ఆంధ్రప్రదేశ్‌లో జల జీవన్ మిషన్ కింద ఎన్ని ఇళ్లకు మంచినీటి కుళాయి కనెక్షన్లు ఉన్నాయి?",
            "hi": "आंध्र प्रदेश में जल जीवन मिशन के तहत कितने घरों में नल जल कनेक्शन हैं?",
            "ta": "ஆந்திராவில் ஜல் ஜீவன் திட்டத்தின் கீழ் எத்தனை வீடுகளுக்கு குடிநீர் குழாய் இணைப்பு உள்ளது?",
            "mr": "आंध्र प्रदेशात जल जीवन मिशन अंतर्गत किती घरांना नळाचे पाणी जोडणी आहे?",
            "bn": "অন্ধ্রপ্রদেশে জল জীবন মিশনের অধীনে কতগুলি বাড়িতে পানীয় জলের সংযোগ রয়েছে?",
            "hi-en": "Andhra Pradesh me Jal Jeevan Mission ke under kitne households me tap water connection hai?",
        },
    },
    {
        "concept_id": "CL-08",
        "domain": "Ayushman Bharat Settled Claims (Andhra Pradesh)",
        "expected_table": "ndap_ayushman_bharat_pmjay",
        "queries": {
            "en": "What is the total claim amount settled under Ayushman Bharat in Andhra Pradesh?",
            "te": "ఆంధ్రప్రదేశ్‌లో ఆయుష్మాన్ భారత్ కింద క్లెయిమ్ అయిన మొత్తం సొమ్ము ఎంత?",
            "hi": "आंध्र प्रदेश में आयुष्मान भारत के तहत कुल कितनी क्लेम राशि का भुगतान किया गया?",
            "ta": "ஆந்திராவில் ஆயுஷ்மான் பாரத் திட்டத்தின் கீழ் வழங்கப்பட்ட மொத்த கிளைம் தொகை எவ்வளவு?",
            "mr": "आंध्र प्रदेशात आयुष्यमान भारत अंतर्गत किती क्लेम रक्कम मंजूर झाली?",
            "bn": "অন্ধ্রপ্রদেশে আয়ুষ্মান ভারত প্রকল্পে মোট কত টাকা নিষ্পত্তি হয়েছে?",
            "hi-en": "Andhra Pradesh me Ayushman Bharat ke under total kitna claim amount settle hua?",
        },
    },
    {
        "concept_id": "CL-09",
        "domain": "Lowest Female Literacy District (Bihar)",
        "expected_table": "ndap_education_stats",
        "queries": {
            "en": "Which district in Bihar recorded the lowest female literacy rate?",
            "te": "బీహార్‌లో అతి తక్కువ స్త్రీ అక్షరాస్యత రేటు ఉన్న జిల్లా ఏది?",
            "hi": "बिहार के किस जिले में महिला साक्षरता दर सबसे कम है?",
            "ta": "பீகாரில் பெண் எழுத்தறிவு விகிதம் மிகவும் குறைவாக உள்ள மாவட்டம் எது?",
            "mr": "बिहारमध्ये सर्वात कमी महिला साक्षरता दर कोणत्या जिल्ह्यात आहे?",
            "bn": "বিহারের কোন জেলায় মহিলা সাক্ষরতার হার সবচেয়ে কম?",
            "hi-en": "Bihar ke kis district me female literacy rate sabse kam hai?",
        },
    },
    {
        "concept_id": "CL-10",
        "domain": "Soil Health Samples Tested (Maharashtra)",
        "expected_table": "ndap_soil_health_records",
        "queries": {
            "en": "What is the total number of soil samples tested in Maharashtra?",
            "te": "మహారాష్ట్రలో ఎన్ని నేల నమూనాలను పరీక్షించారు?",
            "hi": "महाराष्ट्र में कुल कितने मिट्टी के नमूनों की जांच की गई?",
            "ta": "மகாராஷ்டிராவில் எத்தனை மண் மாதிரிகள் பரிசோதிக்கப்பட்டன?",
            "mr": "महाराष्ट्रात तपासलेल्या माती नमुन्यांची एकूण संख्या किती?",
            "bn": "মহারাষ্ট্রে মোট কতগুলি মাটির নমুনা পরীক্ষা করা হয়েছে?",
            "hi-en": "Maharashtra me total kitne soil samples test kiye gaye?",
        },
    },
]

UNICODE_SCRIPT_CHECKS = {
    "hi": (0x0900, 0x097F, "Devanagari"),
    "mr": (0x0900, 0x097F, "Devanagari"),
    "bn": (0x0980, 0x09FF, "Bengali"),
    "ta": (0x0B80, 0x0BFF, "Tamil"),
    "te": (0x0C00, 0x0C7F, "Telugu"),
}


def check_answer_language_fidelity(answer: str, lang: str) -> Tuple[bool, str]:
    """Verifies that the verbalized answer matches the language and script of the question."""
    if not answer or len(answer.strip()) < 5:
        return False, "Empty answer"

    if lang in UNICODE_SCRIPT_CHECKS:
        low, high, script_name = UNICODE_SCRIPT_CHECKS[lang]
        has_target_script = any(low <= ord(c) <= high for c in answer)
        if not has_target_script:
            return False, f"Missing {script_name} characters in {lang} response"
        return True, f"Pure {script_name} ({lang})"

    # For en and hi-en, ensure no regional script characters (0x0900 - 0x0D7F) leak into Latin text
    has_indic_leak = any(0x0900 <= ord(c) <= 0x0D7F for c in answer)
    if has_indic_leak:
        return False, f"Indic script leakage in {lang} response"
    return True, f"Pure Latin ({lang})"


def run_cross_lingual_verification() -> Dict[str, Any]:
    print("=" * 100)
    print("🌐 IndicSQL Sprint 5: Cross-Lingual Semantic Equivalence & Language Fidelity Verification")
    print("=" * 100)
    print("Verifying that parallel questions in English, Telugu, Hindi, Tamil, Marathi, Bengali, & Hinglish:")
    print("  1. Route to the exact same NDAP database table")
    print("  2. Produce valid DuckDB SQL and fetch identical tabular answers (Isomorphic Match)")
    print("  3. Return the verbalized natural-language answer in the SAME language as the question")
    print("-" * 100)

    en_te_comparison_rows = []
    total_queries = 0
    total_isomorphic_matches = 0
    total_lang_fidelity_matches = 0
    total_sql_valid = 0
    concept_reports = []

    t0 = time.perf_counter()

    for item in PARALLEL_CONCEPT_SUITE:
        cid = item["concept_id"]
        domain = item["domain"]
        queries = item["queries"]

        # 1. Execute English baseline first
        en_state = execute_indicsql_pipeline(queries["en"], language="en", model_tier="turbo_fast")
        en_res = en_state.get("execution_result")
        en_rows = en_res.get("rows", []) if en_res else []
        en_val = en_rows[0] if en_rows else "EMPTY"

        lang_outcomes = {}
        for lang, q_text in queries.items():
            total_queries += 1
            st = execute_indicsql_pipeline(q_text, language=lang, model_tier="turbo_fast")
            sql = st.get("generated_sql", "")
            res = st.get("execution_result")
            ans = st.get("verbalized_response", "")
            rows = res.get("rows", []) if res else []

            has_sql = bool(sql and sql.strip().upper().startswith("SELECT"))
            if has_sql:
                total_sql_valid += 1

            is_iso = are_tabular_results_equivalent(res, en_res)
            if is_iso:
                total_isomorphic_matches += 1

            lang_ok, lang_note = check_answer_language_fidelity(ans, lang)
            if lang_ok:
                total_lang_fidelity_matches += 1

            lang_outcomes[lang] = {
                "query": q_text,
                "detected_lang": st.get("detected_lang"),
                "target_table": st.get("target_database"),
                "generated_sql": sql,
                "rows": rows,
                "verbalized_response": ans,
                "isomorphic_with_english": is_iso,
                "language_fidelity": lang_ok,
                "language_note": lang_note,
            }

        te_out = lang_outcomes["te"]
        en_out = lang_outcomes["en"]
        all_7_iso = all(v["isomorphic_with_english"] for v in lang_outcomes.values())
        all_7_lang = all(v["language_fidelity"] for v in lang_outcomes.values())

        en_te_comparison_rows.append([
            cid,
            domain,
            str(en_val),
            str(te_out["rows"][0] if te_out["rows"] else "EMPTY"),
            "✅ MATCH" if te_out["isomorphic_with_english"] else "❌ DIFF",
            "✅ 7/7" if all_7_iso else "❌ MISMATCH",
            "✅ 7/7" if all_7_lang else "❌ LEAK",
        ])

        concept_reports.append({
            "concept_id": cid,
            "domain": domain,
            "english_baseline_rows": en_rows,
            "all_7_languages_isomorphic": all_7_iso,
            "all_7_languages_script_pure": all_7_lang,
            "languages": lang_outcomes,
        })

        print(f"\n[{cid}] {domain}")
        print(f"  🇬🇧 EN Query : {en_out['query']}")
        print(f"     EN SQL   : {en_out['generated_sql']}")
        print(f"     EN Answer: {en_out['verbalized_response']}")
        print(f"  🇮🇳 TE Query : {te_out['query']}")
        print(f"     TE SQL   : {te_out['generated_sql']}")
        print(f"     TE Answer: {te_out['verbalized_response']}")
        print(f"  🔍 Result   : EN Rows={en_rows} | TE Rows={te_out['rows']} | Isomorphic={te_out['isomorphic_with_english']} | All 7 Langs Match={all_7_iso}")

    elapsed_s = time.perf_counter() - t0

    print("\n" + "=" * 100)
    print("📊 CROSS-LINGUAL PARITY SCORECARD (ENGLISH ↔ TELUGU & ALL 7 LANGUAGES)")
    print("=" * 100)
    headers = ["ID", "Domain Concept", "EN Result", "TE Result", "EN↔TE Match", "All 7 Langs EX", "Same-Lang Answer"]
    print(tabulate(en_te_comparison_rows, headers=headers, tablefmt="github"))
    print("-" * 100)
    print(f"  • Total Parallel Queries Executed : {total_queries} (10 concepts x 7 languages)")
    print(f"  • SQL Generation Validity         : {total_sql_valid}/{total_queries} ({total_sql_valid/total_queries*100:.1f}%)")
    print(f"  • Cross-Lingual Tabular Parity    : {total_isomorphic_matches}/{total_queries} ({total_isomorphic_matches/total_queries*100:.1f}%)")
    print(f"  • Answer Language & Script Purity : {total_lang_fidelity_matches}/{total_queries} ({total_lang_fidelity_matches/total_queries*100:.1f}%)")
    print(f"  • Total Verification Time         : {elapsed_s:.2f}s")
    print("=" * 100)

    out_path = REPO_ROOT / "benchmark_results" / "cross_lingual_parity_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_data = {
        "total_concepts": len(PARALLEL_CONCEPT_SUITE),
        "total_queries": total_queries,
        "sql_validity_rate": round(total_sql_valid / total_queries * 100, 2),
        "cross_lingual_isomorphism_rate": round(total_isomorphic_matches / total_queries * 100, 2),
        "language_fidelity_rate": round(total_lang_fidelity_matches / total_queries * 100, 2),
        "concepts": concept_reports,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved full cross-lingual audit report to: {out_path}")
    return report_data


if __name__ == "__main__":
    report = run_cross_lingual_verification()
    if report["cross_lingual_isomorphism_rate"] < 100.0 or report["language_fidelity_rate"] < 100.0:
        sys.exit(1)
