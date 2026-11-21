"""
FastAPI Server Gateway for IndicSQL Swarm.
Exposes endpoints for natural language queries, schema inspection, and benchmark execution.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from indicsql import __version__
from indicsql.agents.critic import validate_sql_security
from indicsql.agents.sandbox_executor import _sandbox
from indicsql.graph.workflow import execute_indicsql_pipeline
from indicsql.models.sarvam_client import SarvamAPIError, SarvamClient
from indicsql.sandbox.validator import validate_and_limit_sql
from indicsql.schema.catalog import NDAPCatalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

app = FastAPI(
    title="IndicSQL API Gateway",
    description="Cross-Lingual Text-to-SQL Swarm for Indian Languages (NDAP Benchmark)",
    version=__version__,
)

# Enable CORS for local frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question in Indic language or Hinglish")
    language: Optional[Literal["en", "hi", "hi-en", "mr", "bn", "ta", "te"]] = Field(
        default=None,
        description="Optional supported language override; omitted means automatic detection.",
    )
    session_id: Optional[str] = Field(
        default=None, description="Optional persistent session identifier"
    )


class QueryResponse(BaseModel):
    query_id: str
    raw_query: str
    detected_language: str
    detected_script: str
    generated_sql: str
    raw_stochastic_sql: Optional[str] = None
    verbalized_response: str
    execution_result: Optional[Dict[str, Any]] = None
    audit_trace: List[Dict[str, Any]] = Field(default_factory=list)


class SqlInspectRequest(BaseModel):
    sql: str = Field(..., description="Read-only SQL to validate and run in the NDAP sandbox")


@app.get("/")
@app.get("/ui")
@app.get("/app")
def serve_frontend_ui():
    """Serves the interactive frontend web application matching the design mockup."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    next_out = repo_root / "frontend" / "out" / "index.html"
    if next_out.exists():
        return FileResponse(next_out)
    return {
        "service": "IndicSQL Agent Swarm",
        "version": __version__,
        "status": "healthy",
        "supported_languages": ["hi", "bn", "ta", "te", "mr", "hi-en", "en"],
        "docs_url": "/docs",
        "studio_frontend": "Run 'npm run dev' inside frontend/ for the full Next.js Studio Cockpit",
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


@app.get("/analytics")
def get_project_analytics():
    """Returns checked-in benchmark and failure artifacts for dashboard views."""
    artifact_paths = {
        "benchmark": REPOSITORY_ROOT / "data" / "benchmarks" / "unseen_140_evaluation_report.json",
        "models": REPOSITORY_ROOT / "data" / "benchmarks" / "baseline_models_matrix.json",
        "failures": REPOSITORY_ROOT / "reports" / "e2e_failure_audit.json",
        "benchmark_queries": REPOSITORY_ROOT / "data" / "benchmarks" / "indicdb_unseen_suite_140.json",
    }
    missing = [str(path) for path in artifact_paths.values() if not path.is_file()]
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Analytics artifacts are missing: {', '.join(missing)}",
        )

    try:
        return {
            key: json.loads(path.read_text(encoding="utf-8"))
            for key, path in artifact_paths.items()
        }
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500, detail=f"Could not load project analytics: {exc}"
        ) from exc


@app.post("/sql/inspect")
def inspect_sql(request: SqlInspectRequest):
    """Validates and executes a read-only SQL statement in the existing sandbox."""
    if not request.sql.strip():
        raise HTTPException(status_code=400, detail="SQL cannot be empty.")

    if not validate_sql_security(request.sql):
        return {
            "valid": False,
            "sql": request.sql,
            "message": "SQL was rejected: only a valid read-only SELECT or WITH statement is allowed.",
            "execution_result": None,
        }

    is_valid, sanitized_sql = validate_and_limit_sql(request.sql)
    if not is_valid:
        return {
            "valid": False,
            "sql": request.sql,
            "message": sanitized_sql,
            "execution_result": None,
        }

    try:
        result = _sandbox.execute_query(sanitized_sql)
    except Exception as exc:
        return {
            "valid": False,
            "sql": sanitized_sql,
            "message": f"SQL passed read-only checks but could not execute: {exc}",
            "execution_result": None,
        }

    return {
        "valid": True,
        "sql": sanitized_sql,
        "message": "Read-only SQL validated and executed successfully.",
        "execution_result": result,
    }


@app.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest):
    """
    Submits a natural language query through the multi-agent pipeline:
    Normalization -> Schema Linking -> SQL Synthesis -> AST Linter -> DuckDB Sandbox -> Verbalizer.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result_state = execute_indicsql_pipeline(request.query, language=request.language)

    return QueryResponse(
        query_id=result_state.get("query_id", ""),
        raw_query=result_state.get("raw_query", ""),
        detected_language=result_state.get("detected_lang", "unknown"),
        detected_script=result_state.get("detected_script", "unknown"),
        generated_sql=result_state.get("generated_sql", ""),
        raw_stochastic_sql=result_state.get("raw_stochastic_sql", ""),
        verbalized_response=result_state.get("verbalized_response", ""),
        execution_result=result_state.get("execution_result"),
        audit_trace=result_state.get("audit_trace", []),
    )


class VoiceSynthesisRequest(BaseModel):
    text: str = Field(..., description="Vernacular text to synthesize into speech")
    language_code: str = Field(
        default="hi-IN",
        description="Target language BCP-47 code (e.g. hi-IN, mr-IN, bn-IN, ta-IN, te-IN)",
    )
    speaker: str = Field(default="meera", description="Speaker voice identifier")


@app.post("/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribes audio using Sarvam Saaras model with automatic language detection.
    """
    client = SarvamClient()
    if not client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Sarvam API is not configured. Please set SARVAM_API_KEY in your .env file.",
        )
    content = await file.read()
    try:
        return client.speech_to_text(content, filename=file.filename or "audio.wav")
    except SarvamAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/voice/synthesize")
def synthesize_speech(request: VoiceSynthesisRequest):
    """
    Synthesizes vernacular audio using Sarvam Bulbul model.
    """
    client = SarvamClient()
    if not client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Sarvam API is not configured. Please set SARVAM_API_KEY in your .env file.",
        )
    try:
        return client.text_to_speech(
            text=request.text,
            target_language_code=request.language_code,
            speaker=request.speaker,
        )
    except SarvamAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
