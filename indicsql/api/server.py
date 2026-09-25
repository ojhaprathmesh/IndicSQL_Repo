"""
FastAPI Server Gateway for IndicSQL Swarm.
Exposes endpoints for natural language queries, schema inspection, and benchmark execution.
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from indicsql import __version__
from indicsql.graph.workflow import execute_indicsql_pipeline
from indicsql.schema.catalog import NDAPCatalog

app = FastAPI(
    title="IndicSQL API Gateway",
    description="Cross-Lingual Text-to-SQL Swarm for Indian Languages (NDAP Benchmark)",
    version=__version__,
)


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question in Indic language or Hinglish")
    session_id: Optional[str] = Field(default=None, description="Optional persistent session identifier")


class QueryResponse(BaseModel):
    query_id: str
    raw_query: str
    detected_language: str
    detected_script: str
    generated_sql: str
    verbalized_response: str
    execution_result: Optional[Dict[str, Any]] = None
    audit_trace: List[Dict[str, Any]] = Field(default_factory=list)


@app.get("/")
def root():
    return {
        "service": "IndicSQL Agent Swarm",
        "version": __version__,
        "status": "healthy",
        "supported_languages": ["hi", "bn", "ta", "te", "mr", "hi-en", "en"],
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/schemas")
def list_schemas():
    """Returns the list of available NDAP benchmark schemas."""
    tables = NDAPCatalog.list_tables()
    return {
        "count": len(tables),
        "tables": {t: NDAPCatalog.get_table_schema(t) for t in tables},
    }


@app.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest):
    """
    Submits a natural language query through the multi-agent pipeline:
    Normalization -> Schema Linking -> SQL Synthesis -> AST Linter -> DuckDB Sandbox -> Verbalizer.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result_state = execute_indicsql_pipeline(request.query)

    return QueryResponse(
        query_id=result_state.get("query_id", ""),
        raw_query=result_state.get("raw_query", ""),
        detected_language=result_state.get("detected_lang", "unknown"),
        detected_script=result_state.get("detected_script", "unknown"),
        generated_sql=result_state.get("generated_sql", ""),
        verbalized_response=result_state.get("verbalized_response", ""),
        execution_result=result_state.get("execution_result"),
        audit_trace=result_state.get("audit_trace", []),
    )
