"""
tests/test_cross_lingual_parity.py
Sprint 5 Unit & Integration Tests for Cross-Lingual Semantic Equivalence.

Verifies:
1. Parallel questions in English and Telugu (plus Hindi, Tamil, Marathi, Bengali, Hinglish)
   fetch identical tabular data from DuckDB (Tabular Isomorphism).
2. Both executable SQL and a localized natural-language answer are returned.
3. The verbalized answer is strictly in the same language and script as the query.
"""

import unittest
from fastapi.testclient import TestClient

from indicsql.api.server import app
from indicsql.benchmark.evaluator import are_tabular_results_equivalent
from indicsql.graph.workflow import execute_indicsql_pipeline
from scripts.verify_cross_lingual_parity import (
    PARALLEL_CONCEPT_SUITE,
    check_answer_language_fidelity,
)


class TestCrossLingualParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_english_vs_telugu_exact_answer_matching(self):
        """
        Tests asking the exact same question in English and Telugu and verifies
        that both fetch identical database rows and return answers in their respective languages.
        """
        for concept in PARALLEL_CONCEPT_SUITE:
            cid = concept["concept_id"]
            en_q = concept["queries"]["en"]
            te_q = concept["queries"]["te"]

            en_state = execute_indicsql_pipeline(en_q, model_tier="turbo_fast")
            te_state = execute_indicsql_pipeline(te_q, model_tier="turbo_fast")

            # 1. Both must generate valid SQL targeting the expected table
            self.assertEqual(en_state.get("target_database"), concept["expected_table"], f"{cid} EN table mismatch")
            self.assertEqual(te_state.get("target_database"), concept["expected_table"], f"{cid} TE table mismatch")
            self.assertTrue(en_state.get("generated_sql", "").upper().startswith("SELECT"))
            self.assertTrue(te_state.get("generated_sql", "").upper().startswith("SELECT"))

            # 2. Both must return identical database execution results (Isomorphic Match)
            en_res = en_state.get("execution_result")
            te_res = te_state.get("execution_result")
            self.assertTrue(
                are_tabular_results_equivalent(en_res, te_res),
                f"[{cid}] English vs Telugu result mismatch! EN={en_res} vs TE={te_res}",
            )

            # 3. English answer must be in Latin script; Telugu answer must be in Telugu script
            en_ans = en_state.get("verbalized_response", "")
            te_ans = te_state.get("verbalized_response", "")
            en_ok, en_msg = check_answer_language_fidelity(en_ans, "en")
            te_ok, te_msg = check_answer_language_fidelity(te_ans, "te")
            self.assertTrue(en_ok, f"[{cid}] EN fidelity failed: {en_msg} ({en_ans})")
            self.assertTrue(te_ok, f"[{cid}] TE fidelity failed: {te_msg} ({te_ans})")

    def test_all_7_languages_cross_lingual_isomorphism(self):
        """Verifies all 7 languages return identical data and native script responses across the parallel suite."""
        for concept in PARALLEL_CONCEPT_SUITE:
            cid = concept["concept_id"]
            en_state = execute_indicsql_pipeline(concept["queries"]["en"], language="en", model_tier="turbo_fast")
            en_res = en_state.get("execution_result")

            for lang, query_text in concept["queries"].items():
                st = execute_indicsql_pipeline(query_text, language=lang, model_tier="turbo_fast")
                res = st.get("execution_result")
                ans = st.get("verbalized_response", "")

                self.assertTrue(
                    are_tabular_results_equivalent(res, en_res),
                    f"[{cid} ({lang})] Result mismatch vs English! EN={en_res} vs {lang}={res}",
                )
                lang_ok, lang_msg = check_answer_language_fidelity(ans, lang)
                self.assertTrue(lang_ok, f"[{cid} ({lang})] Language fidelity failed: {lang_msg}")

    def test_api_endpoint_english_and_telugu_parity(self):
        """Verifies via FastAPI /query endpoint that English and Telugu queries return matching data and same-lang answers."""
        en_resp = self.client.post(
            "/query",
            json={
                "query": "What is the total production of wheat in Punjab in tonnes?",
                "model_tier": "turbo_fast",
            },
        )
        te_resp = self.client.post(
            "/query",
            json={
                "query": "పంజాబ్‌లో గోధుమ మొత్తం ఉత్పత్తి ఎన్ని టన్నులు?",
                "model_tier": "turbo_fast",
            },
        )
        self.assertEqual(en_resp.status_code, 200)
        self.assertEqual(te_resp.status_code, 200)

        en_body = en_resp.json()
        te_body = te_resp.json()

        self.assertEqual(en_body["detected_language"], "en")
        self.assertEqual(te_body["detected_language"], "te")
        self.assertEqual(en_body["execution_result"]["rows"], te_body["execution_result"]["rows"])
        self.assertTrue(any(0x0C00 <= ord(c) <= 0x0C7F for c in te_body["verbalized_response"]))


if __name__ == "__main__":
    unittest.main()
