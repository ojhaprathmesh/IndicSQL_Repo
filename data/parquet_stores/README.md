# NDAP Parquet Storage

This directory holds compressed Apache Parquet (`.parquet`) datasets for all 20 Government of India NDAP benchmark databases.

## Generation:
Parquet tables can be regenerated at any time with:
```bash
uv run python indicsql/schema/ingest_ndap.py
```

DuckDB reads and queries these parquet files in-memory without conversion overhead.
