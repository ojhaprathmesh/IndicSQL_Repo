"""
Cross-Lingual Schema-Linking Agent.
Maps vernacular and transliterated tokens to exact English database tables and columns.
Addresses the 20% schema-linking error diagnosed in the IndicDB benchmark.
"""

from typing import Any, Dict, List

from indicsql.core.state import IndicSQLState, SchemaElement
from indicsql.events.bus import EventBus
from indicsql.events.schemas import SchemaLinkedEvent
from indicsql.schema.multilingual_index import NDAP_MULTILINGUAL_INDEX
from indicsql.schema.phonetic import normalize_indic_phonetics


def link_schema_elements(query: str, lang: str = "en") -> List[SchemaElement]:
    """
    Identifies database tables and columns based on phonetic transliteration
    and dense cross-lingual multilingual index matching across all 20 NDAP databases.
    """
    # Normalize query phonetically
    normalized = normalize_indic_phonetics(query, target_lang=lang)
    search_space = f"{query.lower()} {normalized.lower()}"

    scored_elements: List[tuple[int, SchemaElement]] = []

    for key, meta in NDAP_MULTILINGUAL_INDEX.items():
        score = 0
        for syn in meta["synonyms"]:
            syn_lower = syn.lower()
            if syn_lower in search_space:
                # Longer matches get higher weight
                score += max(len(syn_lower), 3)

        if score > 0:
            scored_elements.append(
                (
                    score,
                    {
                        "table_name": meta["table"],
                        "column_name": meta["column"],
                        "data_type": meta["data_type"],
                        "indic_synonyms": meta["synonyms"][:5],
                        "is_foreign_key": False,
                        "foreign_target": None,
                    },
                )
            )

    # Sort candidates by match weight descending
    scored_elements.sort(key=lambda x: x[0], reverse=True)
    matched_elements = [el for _, el in scored_elements]

    # Morphological stem fallback before defaulting to PM-KISAN
    if not matched_elements:
        _stem_routes = [
            (("produc", "grain", "harvest", "yield", "cereal", "crop"), "ndap_crop_production_census", "production_tonnes", "DOUBLE"),
            (("cultivat", "hectare", "sown"), "ndap_crop_production_census", "area_hectares", "DOUBLE"),
            (("fertiliz", "urea", "dap"), "ndap_fertilizer_distribution", "sales_tonnes", "DOUBLE"),
            (("literac", "litrac", "educat", "sakshar"), "ndap_education_stats", "female_literacy_rate", "FLOAT"),
            (("school",), "ndap_school_infrastructure", "schools_with_electricity", "INTEGER"),
            (("phc", "health", "hospital"), "ndap_rural_health_infrastructure", "primary_health_centres_phc", "INTEGER"),
            (("water", "tap"), "ndap_jal_jeevan_tap_water", "tap_water_connections", "BIGINT"),
            (("road", "pmgsy"), "ndap_pmgsy_rural_roads", "completed_road_length_km", "DOUBLE"),
            (("hous", "pmay"), "ndap_pmay_rural_housing", "houses_completed", "BIGINT"),
            (("mgnrega", "manday", "employ"), "mgnrega_state_annual_employment", "total_mandays_generated", "BIGINT"),
            (("mandi", "price"), "ndap_mandi_commodity_prices", "modal_price_inr", "DOUBLE"),
            (("soil",), "ndap_soil_health_records", "samples_tested", "BIGINT"),
            (("skill", "train", "vocational"), "ndap_vocational_skill_training", "certified_candidates", "BIGINT"),
        ]
        for stems, tbl, col, dtype in _stem_routes:
            if any(st in search_space for st in stems):
                matched_elements.append(
                    {
                        "table_name": tbl,
                        "column_name": col,
                        "data_type": dtype,
                        "indic_synonyms": list(stems[:3]),
                        "is_foreign_key": False,
                        "foreign_target": None,
                    }
                )
                break

    # If completely unmapped, mark with explicit unmapped sentinel
    if not matched_elements:
        matched_elements.append(
            {
                "table_name": "ndap_unmapped_out_of_scope",
                "column_name": "unmapped",
                "data_type": "UNKNOWN",
                "indic_synonyms": ["unmapped"],
                "is_foreign_key": False,
                "foreign_target": None,
            }
        )

    return matched_elements


def schema_linker_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Schema Linker Node: Extracts relevant tables/columns for the canonical query.
    Emits SchemaLinkedEvent on the EventBus.
    """
    canonical_query = state.get("canonical_query", state.get("raw_query", ""))
    lang = state.get("detected_lang", "en")

    pruned = link_schema_elements(canonical_query, lang)
    is_out_of_scope = len(pruned) == 1 and pruned[0].get("table_name") == "ndap_unmapped_out_of_scope"

    existing_target = state.get("target_database")
    if existing_target:
        primary_table = existing_target
    else:
        primary_table = pruned[0]["table_name"] if (pruned and not is_out_of_scope) else "ndap_unmapped_out_of_scope"
    matched_cols = [el["column_name"] for el in pruned]

    # Dynamic schema-linking confidence score based on match count and specificity
    match_density = sum(len(el.get("indic_synonyms", [])) for el in pruned)
    confidence = 0.10 if is_out_of_scope else (min(0.98, max(0.45, round(0.50 + (match_density * 0.05), 2))) if pruned else 0.40)

    EventBus.publish(
        SchemaLinkedEvent(
            query_id=state.get("query_id"),
            target_table=primary_table,
            matched_columns=matched_cols,
            confidence=confidence,
        )
    )

    audit_entry = {
        "step": 2,
        "agent": "SchemaLinkerAgent",
        "action": "cross_lingual_lookup",
        "matched_table": primary_table,
        "matched_columns": matched_cols,
        "confidence": confidence,
        "is_out_of_scope": is_out_of_scope,
    }

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "pruned_schema": pruned,
        "target_database": primary_table,
        "is_out_of_scope": is_out_of_scope,
        "audit_trace": current_trace,
    }
