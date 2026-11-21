import unittest

from indicsql.agents.sql_synthesizer import _build_multi_entity_groupby
from indicsql.schema.catalog import NDAPCatalog


def _sql(table, q):
    return _build_multi_entity_groupby(table, NDAPCatalog.get_table_schema(table), q)


class TestMultiEntityGroupBy(unittest.TestCase):
    def test_two_states_two_crops(self):
        sql = _sql(
            "ndap_crop_production_census",
            "what is the total production of wheat and rice crops in Punjab and Haryana separately",
        )
        self.assertIsNotNone(sql)
        self.assertIn("GROUP BY state_name, crop_name", sql)
        self.assertIn("'PUNJAB'", sql)
        self.assertIn("'HARYANA'", sql)
        self.assertIn("'WHEAT'", sql)
        self.assertIn("'RICE'", sql)

    def test_single_entity_untouched(self):
        self.assertIsNone(_sql("ndap_crop_production_census", "total wheat production in Punjab"))

    def test_full_pipeline_keeps_group_by_and_answers_all_entities(self):
        from indicsql.graph.workflow import execute_indicsql_pipeline

        s = execute_indicsql_pipeline(
            "what is the total production of wheat and rice crops in Punjab and Haryana separately"
        )
        self.assertIn("GROUP BY", s["generated_sql"])
        self.assertEqual(len(s["execution_result"]["rows"]), 4)
        answer = s["verbalized_response"]
        for token in ("Punjab", "Haryana", "Wheat", "Rice"):
            self.assertIn(token, answer)

    def test_grains_produced_typo_state_and_last_two_years(self):
        from indicsql.graph.workflow import execute_indicsql_pipeline

        s = execute_indicsql_pipeline(
            "and what about total grains produced by haryan in last two years from now"
        )
        self.assertEqual(s["target_database"], "ndap_crop_production_census")
        self.assertIn("state_name = 'HARYANA'", s["generated_sql"])
        self.assertIn("LIMIT 2", s["generated_sql"])
        self.assertEqual(s["execution_result"]["rows"], [[42033871.0]])
        self.assertIn("Haryana", s["verbalized_response"])
        self.assertIn("4.20 Crores", s["verbalized_response"])


if __name__ == "__main__":
    unittest.main()
