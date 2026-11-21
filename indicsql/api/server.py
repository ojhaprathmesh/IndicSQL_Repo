"""
FastAPI Server Gateway for IndicSQL Swarm.
Exposes endpoints for natural language queries, schema inspection, and benchmark execution.
"""

import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, Security, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field

from indicsql import __version__
from indicsql.agents.critic import validate_sql_security
from indicsql.agents.sandbox_executor import _sandbox
from indicsql.core.session_store import session_store
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

# In-memory sliding window rate limiter: 60 requests/min per client IP
_RATE_LIMIT_PER_MINUTE = int(os.environ.get("INDICSQL_RATE_LIMIT_PER_MINUTE", "60"))
_RATE_LIMIT_WINDOW = 60.0
_client_timestamps: Dict[str, List[float]] = defaultdict(list)


def check_rate_limit(request: Request) -> None:
    """Enforces per-client IP sliding window rate limit to guard against resource exhaustion."""
    if _RATE_LIMIT_PER_MINUTE <= 0:
        return
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    valid_window = now - _RATE_LIMIT_WINDOW
    _client_timestamps[client_ip] = [
        ts for ts in _client_timestamps[client_ip] if ts > valid_window
    ]
    if len(_client_timestamps[client_ip]) >= _RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {_RATE_LIMIT_PER_MINUTE} queries per minute allowed.",
        )
    _client_timestamps[client_ip].append(now)


# Optional API Key Authentication Header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)):
    """Verifies X-API-Key if INDICSQL_API_KEY environment variable is configured."""
    expected = os.environ.get("INDICSQL_API_KEY", "").strip()
    if expected and api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header.")
    return api_key


# Enable CORS for local and web frontend clients
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


@app.get("/conversations")
def list_conversations(_: Optional[str] = Depends(verify_api_key)):
    """Returns all stored multi-turn conversation sessions."""
    return session_store.list_conversations()


@app.post("/conversations")
def create_conversation(title: str = "New Conversation", _: Optional[str] = Depends(verify_api_key)):
    """Creates a new conversation session."""
    return session_store.create_conversation(title=title)


@app.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str, _: Optional[str] = Depends(verify_api_key)):
    """Retrieves full conversation turns and messages."""
    conv = session_store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv


@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, _: Optional[str] = Depends(verify_api_key)):
    """Deletes a conversation session."""
    success = session_store.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"status": "deleted"}


@app.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest, http_req: Request, _: Optional[str] = Depends(verify_api_key)):
    """
    Submits a natural language query through the multi-agent pipeline:
    Normalization -> Schema Linking -> SQL Synthesis -> AST Linter -> DuckDB Sandbox -> Verbalizer.
    """
    check_rate_limit(http_req)
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result_state = execute_indicsql_pipeline(request.query, language=request.language)

    if request.session_id:
        session_store.add_message(
            conversation_id=request.session_id,
            role="user",
            content=request.query,
        )
        session_store.add_message(
            conversation_id=request.session_id,
            role="assistant",
            content=result_state.get("verbalized_response", ""),
            payload={
                "generated_sql": result_state.get("generated_sql", ""),
                "execution_result": result_state.get("execution_result"),
                "detected_language": result_state.get("detected_lang", "unknown"),
            },
        )

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
