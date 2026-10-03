import unittest

from indicsql.agents.critic import validate_sql_security
from indicsql.agents.schema_linker import schema_linker_node
from indicsql.agents.supervisor import detect_indic_script, identify_language_code
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
        # 1. Safe SELECT, checks automatic LIMIT injection
        safe_sql = "SELECT state_name, SUM(amount_inr) FROM ndap_pm_kisan_disbursement GROUP BY state_name"
        is_safe, regenerated_sql = validate_sql_security(safe_sql)
        self.assertTrue(is_safe)
        self.assertIn("LIMIT 1000", regenerated_sql.upper())

        # Also testing sandbox validator logic if any
        valid, limited_sql = validate_and_limit_sql(safe_sql)
        self.assertTrue(valid)
        self.assertIn("LIMIT 1000", limited_sql)

        # 2. Unsafe mutation (DROP)
        malicious_sql = "DROP TABLE ndap_pm_kisan_disbursement;"
        is_safe, err_msg = validate_sql_security(malicious_sql)
        self.assertFalse(is_safe)
        self.assertIn("Non-SELECT mutation", err_msg)
        
        valid, err = validate_and_limit_sql(malicious_sql)
        self.assertFalse(valid)
        
        # 3. Unsafe mutation (DELETE)
        delete_sql = "DELETE FROM ndap_pm_kisan_disbursement WHERE state_name='Bihar'"
        is_safe, err_msg = validate_sql_security(delete_sql)
        self.assertFalse(is_safe)

        # 4. False-positive names containing forbidden keywords (e.g., "drop")
        false_positive_sql = "SELECT * FROM drop_shipping_data"
        is_safe, fp_sql = validate_sql_security(false_positive_sql)
        self.assertTrue(is_safe)
        self.assertIn("LIMIT 1000", fp_sql.upper())
        
        # 5. Invalid SQL Parse Error
        invalid_sql = "SELECT * FORM table" # intentional typo
        is_safe, err_msg = validate_sql_security(invalid_sql)
        self.assertFalse(is_safe)
        self.assertIn("SQL Parse Error", err_msg)


if __name__ == "__main__":
    unittest.main()
