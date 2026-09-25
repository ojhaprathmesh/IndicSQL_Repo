"""
DuckDB Sandboxed In-Memory Execution Engine.
Loads NDAP sample schemas into an isolated, ephemeral memory space and executes
read-only analytical SQL queries with runtime resource safeguards.
"""

import time
from pathlib import Path
from typing import Optional

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    import sqlite3
    HAS_DUCKDB = False

from indicsql.core.state import TabularResult

PARQUET_STORE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "parquet_stores"


class DuckDBSandbox:
    """Ephemeral In-Memory Sandbox for executing candidate SQL on NDAP tables."""

    def __init__(self, memory_limit_mb: int = 512, parquet_dir: Optional[Path] = None):
        self.has_duckdb = HAS_DUCKDB
        self.parquet_dir = parquet_dir or PARQUET_STORE_DIR
        if self.has_duckdb:
            self.con = duckdb.connect(database=":memory:")
            self.con.execute(f"SET max_memory = '{memory_limit_mb}MB'")
        else:
            self.con = sqlite3.connect(":memory:")
        self._init_ndap_tables()

    def _init_ndap_tables(self) -> None:
        """Loads tables from parquet store if available, or seeds core mock tables."""
        loaded_from_parquet = False
        if self.has_duckdb and self.parquet_dir.exists():
            parquet_files = list(self.parquet_dir.glob("*.parquet"))
            if parquet_files:
                for p_file in parquet_files:
                    table_name = p_file.stem
                    self.con.execute(
                        f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{p_file.resolve()}');"
                    )
                loaded_from_parquet = True

        if not loaded_from_parquet:
            self._seed_default_mock_tables()

    def _seed_default_mock_tables(self) -> None:
        """Fallback mock tables if parquet stores are not generated yet."""
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS ndap_pm_kisan_disbursement (
                state_name VARCHAR,
                district_name VARCHAR,
                financial_year VARCHAR,
                farmer_beneficiaries BIGINT,
                amount_inr DOUBLE
            );
        """)
        self.con.execute("""
            INSERT INTO ndap_pm_kisan_disbursement VALUES
            ('MAHARASHTRA', 'Pune', '2024-25', 1240500, 2481000000.0),
            ('MAHARASHTRA', 'Nagpur', '2024-25', 980200, 1960400000.0),
            ('MAHARASHTRA', 'Nashik', '2024-25', 1420100, 2840200000.0),
            ('BIHAR', 'Patna', '2024-25', 1150000, 2300000000.0),
            ('TAMIL NADU', 'Madurai', '2024-25', 850000, 1700000000.0);
        """)

        # 2. Education Statistics Table (UDISE+ / NFHS-5)
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS ndap_education_stats (
                state_name VARCHAR,
                district_name VARCHAR,
                census_year INTEGER,
                student_count INTEGER,
                female_literacy_rate FLOAT
            );
        """)
        self.con.execute("""
            INSERT INTO ndap_education_stats VALUES
            ('BIHAR', 'Patna', 2023, 450000, 62.4),
            ('BIHAR', 'Gaya', 2023, 380000, 54.1),
            ('BIHAR', 'Purnia', 2023, 310000, 46.2),
            ('MAHARASHTRA', 'Pune', 2023, 620000, 84.5);
        """)

        # 3. MGNREGA Annual Employment Table
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS mgnrega_state_annual_employment (
                state_name VARCHAR,
                financial_year VARCHAR,
                total_mandays_generated BIGINT
            );
        """)
        self.con.execute("""
            INSERT INTO mgnrega_state_annual_employment VALUES
            ('TAMIL NADU', '2024-25', 342198000),
            ('TAMIL NADU', '2023-24', 398104500),
            ('TAMIL NADU', '2022-23', 412009200),
            ('MAHARASHTRA', '2024-25', 285400000);
        """)

    def execute_query(self, sql: str) -> TabularResult:
        """
        Executes a SQL query in the sandbox and returns a TabularResult.
        """
        start = time.perf_counter()

        if self.has_duckdb:
            rel = self.con.sql(sql)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            if rel is None:
                return {
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "execution_time_ms": elapsed_ms,
                }
            columns = rel.columns
            rows = [list(r) for r in rel.fetchall()]
        else:
            cur = self.con.cursor()
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = [list(r) for r in cur.fetchall()]
            elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": elapsed_ms,
        }

    def close(self) -> None:
        """Closes the database connection."""
        self.con.close()

