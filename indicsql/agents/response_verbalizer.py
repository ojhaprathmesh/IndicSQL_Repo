"""
Response Verbalizer Agent.
Takes tabular SQL execution results and verbalizes fluent, concise natural language answers
in the citizen's mother tongue (Hindi, Marathi, Tamil, Telugu, Bengali, Hinglish, English)
with localized Indian numbering (Lakhs and Crores).
"""

from typing import Any, Dict, List
from indicsql.core.state import IndicSQLState


def format_indian_currency_number(val: float) -> str:
    """Formats large integers/floats into Crores or Lakhs."""
    if val >= 10_000_000:
        crores = val / 10_000_000
        return f"{crores:.2f} कोटी (Crores)"
    if val >= 100_000:
        lakhs = val / 100_000
        return f"{lakhs:.2f} लाख (Lakhs)"
    return f"{val:,.0f}"


def verbalize_tabular_result(state: IndicSQLState) -> str:
    """Produces the localized natural language explanation."""
    res = state.get("execution_result")
    err = state.get("execution_error")
    lang = state.get("detected_lang", "en")
    raw = state.get("raw_query", "")

    if err or not res:
        if lang == "hi":
            return f"माफ़ कीजिए, डेटाबेस में आपके प्रश्न का सटीक उत्तर नहीं मिल सका। (त्रुटि: {err or 'कोई डेटा नहीं'})"
        elif lang == "mr":
            return f"क्षमस्व, डेटाबेसमध्ये आपल्या प्रश्नाचे उत्तर सापडू शकले नाही. (त्रुटी: {err or 'डेटा उपलब्ध नाही'})"
        return f"Unable to retrieve data for query. (Reason: {err or 'Empty result set'})"

    rows = res.get("rows", [])
    if not rows:
        return "डेटाबेस में कोई रिकॉर्ड नहीं मिला। (No matching records found in database)."

    row = rows[0]
    # Check for PM-KISAN Aggregates
    if len(row) == 2 and isinstance(row[0], (int, float)) and isinstance(row[1], (int, float)):
        farmers = row[0]
        amount = row[1]
        farmers_fmt = format_indian_currency_number(float(farmers))
        amount_fmt = format_indian_currency_number(float(amount))

        if lang == "mr":
            return (
                f"पीएम-किसान योजनेअंतर्गत एकूण {farmers_fmt} शेतकऱ्यांना लाभ मिळाला, "
                f"आणि ₹{amount_fmt} ची रक्कम थेट वितरित करण्यात आली."
            )
        elif lang == "hi":
            return (
                f"पीएम-किसान योजना के तहत कुल {farmers_fmt} किसानों को लाभ प्राप्त हुआ, "
                f"और कुल ₹{amount_fmt} की राशि सीधे हस्तांतरित की गई।"
            )
        elif lang == "hi-en":
            return (
                f"PM-KISAN yojana ke tahat total {farmers_fmt} farmers ko labh mila, "
                f"aur kul ₹{amount_fmt} amount directly disburse hua."
            )
        else:
            return (
                f"Under the PM-KISAN scheme, a total of {farmers:,} farmers received benefits, "
                f"with an aggregate disbursement of ₹{amount:,.2f} INR."
            )

    return f"Execution successful. Retrieved {len(rows)} record(s). Sample: {rows[:3]}"


def response_verbalizer_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Verbalizer Node: Formulates vernacular answer.
    """
    answer = verbalize_tabular_result(state)

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
