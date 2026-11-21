"""
Unit Tests for Centralized Session and Conversation Storage in FastAPI.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient

from indicsql.api.server import app
from indicsql.core.session_store import SessionStore


class TestSessionStoreAndAPI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_sessions.db"
        self.store = SessionStore(db_path=self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_store_conversation_crud(self):
        conv = self.store.create_conversation(title="Test Agriculture Query")
        self.assertEqual(conv["title"], "Test Agriculture Query")

        self.store.add_message(conv["id"], role="user", content="How many farmers in Bihar?")
        self.store.add_message(
            conv["id"],
            role="assistant",
            content="There are 7,500,000 farmers.",
            payload={"sql": "SELECT 7500000;"},
        )

        loaded = self.store.get_conversation(conv["id"])
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded["messages"]), 2)
        self.assertEqual(loaded["messages"][0]["role"], "user")
        self.assertEqual(loaded["messages"][1]["payload"]["sql"], "SELECT 7500000;")

        # Test listing
        all_convs = self.store.list_conversations()
        self.assertEqual(len(all_convs), 1)

        # Test deletion
        deleted = self.store.delete_conversation(conv["id"])
        self.assertTrue(deleted)
        self.assertIsNone(self.store.get_conversation(conv["id"]))

    def test_api_conversation_routes(self):
        res = self.client.get("/conversations")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

        create_res = self.client.post("/conversations?title=API%20Test%20Chat")
        self.assertEqual(create_res.status_code, 200)
        cid = create_res.json()["id"]

        get_res = self.client.get(f"/conversations/{cid}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["title"], "API Test Chat")

        del_res = self.client.delete(f"/conversations/{cid}")
        self.assertEqual(del_res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
