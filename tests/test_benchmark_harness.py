"""
Unit tests for the IndicDB Benchmark Evaluation Harness (Phase 1: p1_2).
"""

import unittest

from indicsql.benchmark.dataset import BenchmarkQuery, load_benchmark_dataset
from indicsql.benchmark.evaluator import (
    IndicDBEvaluator,
    are_tabular_results_equivalent,
    compute_schema_linking_f1,
)


class TestBenchmarkHarness(unittest.TestCase):
    def test_dataset_loading(self):
        queries = load_benchmark_dataset()
        self.assertGreaterEqual(len(queries), 18)

        languages = {q.language for q in queries}
        expected_langs = {"hi", "mr", "ta", "te", "bn", "hi-en", "en"}
        self.assertEqual(languages, expected_langs, "Benchmark must cover all 7 IndicDB languages.")

    def test_tabular_isomorphism_equivalence(self):
        res1 = {
            "columns": ["state", "val"],
            "rows": [["MAHARASHTRA", 100], ["BIHAR", 200]],
            "row_count": 2,
            "execution_time_ms": 1.0,
        }
        # Order reversed rows (multiset identical)
        res2 = {
            "columns": ["state", "val"],
            "rows": [["BIHAR", 200.0], ["MAHARASHTRA", 100.0]],
            "row_count": 2,
            "execution_time_ms": 1.0,
        }
        self.assertTrue(are_tabular_results_equivalent(res1, res2))

        # Different values
        res3 = {
            "columns": ["state", "val"],
            "rows": [["MAHARASHTRA", 100], ["BIHAR", 205]],
            "row_count": 2,
            "execution_time_ms": 1.0,
        }
        self.assertFalse(are_tabular_results_equivalent(res1, res3))

    def test_schema_f1_computation(self):
        predicted = [
            {"column_name": "farmer_beneficiaries"},
            {"column_name": "amount_inr"},
            {"column_name": "state_name"},
        ]
        gold = ["farmer_beneficiaries", "amount_inr", "state_name"]
        f1 = compute_schema_linking_f1(predicted, gold)
        self.assertAlmostEqual(f1, 1.0)

        # Partial match
        predicted_partial = [{"column_name": "farmer_beneficiaries"}]
        f1_partial = compute_schema_linking_f1(predicted_partial, gold)
        self.assertGreater(f1_partial, 0.0)
        self.assertLess(f1_partial, 1.0)

    def test_evaluator_single_query(self):
        evaluator = IndicDBEvaluator()
        bq = BenchmarkQuery(
            query_id="test-en-01",
            query="What is the total number of farmer beneficiaries under PM-KISAN in Maharashtra?",
            language="en",
            script="Latin",
            domain="Agriculture",
            target_table="ndap_pm_kisan_disbursement",
            gold_sql="SELECT SUM(farmer_beneficiaries) AS total_farmers, SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';",
            difficulty="medium",
            target_columns=["farmer_beneficiaries", "amount_inr", "state_name"],
        )
        result = evaluator.evaluate_query(bq)
        self.assertTrue(result.execution_match)
        self.assertGreaterEqual(result.schema_f1, 0.5)


if __name__ == "__main__":
    unittest.main()
