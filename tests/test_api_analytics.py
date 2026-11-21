import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from indicsql.api.server import app


class TestAnalyticsAndSqlInspectionEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_analytics_returns_checked_in_project_artifacts(self):
        response = self.client.get("/analytics")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["benchmark"]["total_queries"], 140)
        self.assertEqual(len(payload["benchmark"]["language_scorecards"]), 7)
        self.assertEqual(len(payload["benchmark_queries"]), 140)
        self.assertGreater(len(payload["models"]["models"]), 0)
        self.assertGreater(len(payload["failures"]["traces"]), 0)

    def test_sql_inspection_executes_read_only_query(self):
        response = self.client.post(
            "/sql/inspect",
            json={"sql": "SELECT 42 AS answer"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["execution_result"]["rows"], [[42]])

    def test_sql_inspection_rejects_mutation(self):
        response = self.client.post(
            "/sql/inspect",
            json={"sql": "DROP TABLE ndap_pm_kisan_disbursement"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["valid"])
        self.assertIsNone(payload["execution_result"])

    @patch("indicsql.api.server.execute_indicsql_pipeline")
    def test_query_endpoint_forwards_selected_language(self, execute_pipeline):
        execute_pipeline.return_value = {
            "query_id": "test-query",
            "raw_query": "Show all farmers",
            "detected_lang": "hi",
            "detected_script": "Latin",
            "generated_sql": "SELECT 1",
            "verbalized_response": "उत्तर",
            "execution_result": None,
            "audit_trace": [],
        }

        response = self.client.post(
            "/query",
            json={"query": "Show all farmers", "language": "hi"},
        )

        self.assertEqual(response.status_code, 200)
        execute_pipeline.assert_called_once_with(
            "Show all farmers", language="hi", model_tier="trained_pro"
        )
        self.assertEqual(response.json()["detected_language"], "hi")

    def test_query_endpoint_rejects_unsupported_language(self):
        response = self.client.post(
            "/query",
            json={"query": "Show all farmers", "language": "fr"},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
