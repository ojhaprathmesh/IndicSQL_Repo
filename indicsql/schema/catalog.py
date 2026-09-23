"""
NDAP Database Catalog Definitions and Schema Registry.
Manages metadata for the 20 National Data & Analytics Platform (NDAP) benchmark databases.
"""

from typing import Dict, List, Any


class NDAPCatalog:
    """Registry of NDAP database schemas, tables, and column data dictionaries."""

    _TABLES: Dict[str, Dict[str, Any]] = {
        "ndap_pm_kisan_disbursement": {
            "domain": "Agriculture",
            "description": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) state and district level fund disbursements.",
            "columns": {
                "state_name": "VARCHAR - State/UT name (e.g. MAHARASHTRA, BIHAR)",
                "district_name": "VARCHAR - District name",
                "financial_year": "VARCHAR - Financial year string (e.g. 2024-25)",
                "farmer_beneficiaries": "BIGINT - Number of farmer accounts credited",
                "amount_inr": "DOUBLE - Total fund amount disbursed in Indian Rupees",
            },
        },
        "ndap_education_stats": {
            "domain": "Education",
            "description": "Unified District Information System for Education Plus (UDISE+) literacy & student enrollment metrics.",
            "columns": {
                "state_name": "VARCHAR - State name",
                "district_name": "VARCHAR - District name",
                "census_year": "INTEGER - Year of report",
                "student_count": "INTEGER - Enrolled student count",
                "female_literacy_rate": "FLOAT - Percentage female literacy rate",
            },
        },
        "mgnrega_state_annual_employment": {
            "domain": "Rural Development",
            "description": "Mahatma Gandhi National Rural Employment Guarantee Scheme annual person-days and wage data.",
            "columns": {
                "state_name": "VARCHAR - State name",
                "financial_year": "VARCHAR - Financial year string",
                "total_mandays_generated": "BIGINT - Person-days of employment generated",
            },
        },
    }

    @classmethod
    def list_tables(cls) -> List[str]:
        """Returns all registered table names."""
        return list(cls._TABLES.keys())

    @classmethod
    def get_table_schema(cls, table_name: str) -> Dict[str, Any]:
        """Returns the schema dictionary for a specific table."""
        return cls._TABLES.get(table_name, {})
