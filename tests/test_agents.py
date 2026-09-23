import unittest
from indicsql.agents.supervisor import detect_indic_script, identify_language_code, supervisor_node
from indicsql.agents.schema_linker import schema_linker_node
from indicsql.agents.critic import validate_sql_security
from indicsql.sandbox.validator import validate_and_limit_sql


class TestAgentNodes(unittest.TestCase):
    def test_script_detection(self):
        self.assertEqual(detect_indic_script("बिहार के किस जिले में"), "Devanagari")
        self.assertEqual(detect_indic_script("தமிழ்நாடு"), "Tamil")
        self.assertEqual(detect_indic_script("రైతులు"), "Telugu")
        self.assertEqual(detect_indic_script("How many farmers"), "Latin")
        self.assertEqual(detect_indic_script("Maharashtra mein kitne kisan"), "Latin")

    def test_language_identification(self):
        self.assertEqual(identify_language_code("தமிழ்நாடு", "Tamil"), "ta")
        self.assertEqual(identify_language_code("రైతులు", "Telugu"), "te")
        self.assertEqual(identify_language_code("Maharashtra mein kitne kisano", "Latin"), "hi-en")
        self.assertEqual(identify_language_code("How many farmers received benefits", "Latin"), "en")
        self.assertEqual(identify_language_code("महाराष्ट्रात किती शेतकऱ्यांना", "Devanagari"), "mr")

    def test_schema_linker(self):
        state = {
            "raw_query": "महाराष्ट्रात किती शेतकऱ्यांना पीएम-किसान योजनेचा लाभ मिळाला?",
            "canonical_query": "महाराष्ट्रात किती शेतकऱ्यांना पीएम-किसान योजनेचा लाभ मिळाला?",
            "detected_lang": "mr",
            "audit_trace": [],
        }
        result = schema_linker_node(state)
        self.assertTrue(len(result["pruned_schema"]) > 0)
        self.assertEqual(result["pruned_schema"][0]["table_name"], "ndap_pm_kisan_disbursement")

    def test_critic_and_ast_validator(self):
        safe_sql = "SELECT state_name, SUM(amount_inr) FROM ndap_pm_kisan_disbursement GROUP BY state_name"
        self.assertTrue(validate_sql_security(safe_sql))
        valid, limited_sql = validate_and_limit_sql(safe_sql)
        self.assertTrue(valid)
        self.assertIn("LIMIT 1000", limited_sql)

        malicious_sql = "DROP TABLE ndap_pm_kisan_disbursement;"
        self.assertFalse(validate_sql_security(malicious_sql))
        valid, err = validate_and_limit_sql(malicious_sql)
        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
