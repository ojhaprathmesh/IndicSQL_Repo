"""
Integration Smoke Test Suite for Mobile App <-> API Gateway Contract.
Verifies endpoints consumed by Flutter mobile client:
- /health & /health/data telemetry
- /query dual-tier routing (trained_pro vs turbo_fast)
- /conversations CRUD session persistence
- /sql/inspect interactive sandbox execution
"""

import unittest
from fastapi.testclient import TestClient

from indicsql.api.server import app


class TestMobileContractSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoints(self):
        # 1. Basic Health Check
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "ok"})

        # 2. Data Sandbox Telemetry Health Check
        res_data = self.client.get("/health/data")
        self.assertEqual(res_data.status_code, 200)
        data = res_data.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("table_count", data)
        self.assertGreater(data["table_count"], 0)
        self.assertIn("total_rows", data)
        self.assertGreater(data["total_rows"], 0)
        self.assertIn("memory_limit_mb", data)

    def test_query_contract_turbo_tier(self):
        payload = {
            "query": "Total farmers in Maharashtra under PM-Kisan",
            "language": "en",
            "model_tier": "turbo_fast",
        }
        res = self.client.post("/query", json=payload)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("query_id", body)
        self.assertEqual(body["model_tier"], "turbo_fast")
        self.assertTrue(body["generated_sql"].upper().startswith("SELECT"))
        self.assertIn("verbalized_response", body)
        self.assertIsInstance(body["execution_result"], dict)

    def test_query_contract_pro_tier(self):
        payload = {
            "query": "Total farmers in Maharashtra under PM-Kisan",
            "language": "en",
            "model_tier": "trained_pro",
        }
        res = self.client.post("/query", json=payload)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("query_id", body)
        self.assertEqual(body["model_tier"], "trained_pro")
        self.assertTrue(body["generated_sql"].upper().startswith("SELECT"))

    def test_conversations_crud_contract(self):
        # 1. Create session
        res_create = self.client.post("/conversations?title=SmokeTestSession")
        self.assertEqual(res_create.status_code, 200)
        conv = res_create.json()
        conv_id = conv["id"]
        self.assertEqual(conv["title"], "SmokeTestSession")

        # 2. Query with session_id
        q_payload = {
            "query": "Show wheat production in Punjab",
            "session_id": conv_id,
            "model_tier": "turbo_fast",
        }
        res_q = self.client.post("/query", json=q_payload)
        self.assertEqual(res_q.status_code, 200)

        # 3. Retrieve conversation turns
        res_get = self.client.get(f"/conversations/{conv_id}")
        self.assertEqual(res_get.status_code, 200)
        history = res_get.json()
        self.assertGreaterEqual(len(history["messages"]), 2)

        # 4. Delete session
        res_del = self.client.delete(f"/conversations/{conv_id}")
        self.assertEqual(res_del.status_code, 200)

    def test_sql_inspect_contract(self):
        payload = {"sql": "SELECT COUNT(*) AS total FROM ndap_pm_kisan_disbursement;"}
        res = self.client.post("/sql/inspect", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["valid"])
        self.assertIsNotNone(data["execution_result"])


if __name__ == "__main__":
    unittest.main()
