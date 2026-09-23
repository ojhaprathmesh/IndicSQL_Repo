import unittest
from indicsql.graph.workflow import execute_indicsql_pipeline


class TestPipeline(unittest.TestCase):
    def test_marathi_pipeline_run(self):
        query = "महाराष्ट्रात गेल्या वर्षी किती शेतकऱ्यांना पीएम-किसानचा लाभ मिळाला?"
        state = execute_indicsql_pipeline(query)

        self.assertEqual(state["detected_lang"], "mr")
        self.assertEqual(state["detected_script"], "Devanagari")
        self.assertNotEqual(state["generated_sql"], "")
        self.assertIsNotNone(state["execution_result"])
        self.assertGreater(state["execution_result"]["row_count"], 0)
        self.assertTrue("शेतकऱ्यांना" in state["verbalized_response"] or "पीएम-किसान" in state["verbalized_response"])
        self.assertGreaterEqual(len(state["audit_trace"]), 4)

    def test_bihar_education_pipeline_run(self):
        query = "बिहार के किस जिले में 2023 में सबसे कम महिला साक्षरता थी?"
        state = execute_indicsql_pipeline(query)

        self.assertEqual(state["detected_lang"], "hi")
        self.assertEqual(state["detected_script"], "Devanagari")
        self.assertIn("female_literacy_rate", state["generated_sql"])
        self.assertIsNotNone(state["execution_result"])


if __name__ == "__main__":
    unittest.main()
