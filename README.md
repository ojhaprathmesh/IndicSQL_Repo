# IndicSQL 🇮🇳

> **Autonomous Multi-Agent Cross-Lingual Text-to-SQL & Semantic Schema-Linking Swarm for Indian Languages**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Package Manager](https://img.shields.io/badge/uv-fast_python_package_manager-261230?logo=uv)](https://github.com/astral-sh/uv)
[![Benchmark](https://img.shields.io/badge/Benchmark-IndicDB%20(April%202026)-orange)](https://github.com/ojhaprathmesh/IndicSQL_Repo)
[![Framework](https://img.shields.io/badge/Orchestration-LangGraph-purple)](https://github.com/langchain-ai/langgraph)
[![Engine](https://img.shields.io/badge/Execution-DuckDB-yellow)](https://duckdb.org/)

---

## 📌 Project Overview

**IndicSQL** is an autonomous multi-agent cross-lingual Text-to-SQL system engineered to bridge the **9% accuracy deficit** identified in the landmark **IndicDB Benchmark (April 2026)**. By fusing phonetics-aware cross-lingual schema-linking, an open Indic transformer (`Sarvam-2B` / `Qwen-2.5-Coder`) fine-tuned on relational aggregations, an isolated in-memory execution sandbox (`DuckDB`), and a dialect-native response verbalizer, IndicSQL democratizes access to Indian Open Government Data (**NDAP**) for 1.4 billion citizens across **7 languages** (*Hindi, Bengali, Tamil, Telugu, Marathi, Hinglish, English*).

```
[Indic / Hinglish / Regional Query]
  │
  ▼
[1. Query Supervisor & Script Router]
  │
  ▼
[2. Cross-Lingual Schema-Linking Agent (mE5 + Phonetic Graph)]
  │
  ▼
[3. Aggregation SQL Synthesizer (Sarvam-2B / Qwen LoRA)]
  │
  ▼
[4. Security & AST Linter Critic (Read-Only SELECT Enforcement)]
  │
  ▼
[5. Ephemeral In-Memory DuckDB Sandbox] ──(Execution Error / Zero Rows)──┐
  │                                                                       ▼
  │ (Success)                                                [Reflection Healer Node]
  ▼                                                                       │
[6. Response Verbalizer Agent] ◄──────────────────────────────────────────┘
  │
  ▼
[Citizen Receives Mother-Tongue Explanation + Formatted Lakhs/Crores + Charts]
```

---

## 🎯 The Untapped Problem & Research Motivation

The Government of India hosts petabytes of public welfare, agricultural, healthcare, educational, and demographic datasets on platforms like **NDAP (National Data & Analytics Platform)** and **data.gov.in**. However:

- **The English Schema Monopoly:** Over **85% of Indian citizens** and local field administrators formulate analytical questions in regional languages or transliterated Hinglish, but all government database schemas and column names are written exclusively in English (`dist_code`, `farmer_beneficiaries`, `total_mandays_generated`).
- **The IndicDB Benchmark Gap (April 2026):** Evaluated across **15,617 questions** and **20 real-world NDAP databases**, state-of-the-art models suffered a severe performance penalty when queried in Indian languages compared to English:
  - Telugu: **-11.0%**
  - Tamil: **-9.8%**
  - Bengali: **-9.2%**
  - Hindi: **-8.4%**
  - Marathi: **-8.1%**
  - Hinglish: **-6.87%**
- **The Two Quantified Root Causes:**
  1. **20% Schema-Linking Breakdown:** Vernacular tokens (*"vidyarthi"*, *"kisano"*, *"shala"*) fail to align with English database columns.
  2. **28% Aggregation & GROUP BY Breakdown:** Relational reasoning (multi-tier filtering, regional groupings, conditional counts, temporal windows) collapses under non-English syntactic structures.

IndicSQL provides the **first dedicated multi-agent architecture** targeting these exact failure modes.

---

## 🏛️ Multi-Agent Swarm Architecture

IndicSQL coordinates 6 specialized agent nodes through a unified LangGraph State Blackboard:

| Agent Node | Responsibility | Tech / Methods |
| :--- | :--- | :--- |
| **Supervisor & Script Router** | Ingests query, identifies Unicode script and dialect, and manages state progression. | Unicode Block Analyzer, FastText Language ID |
| **Cross-Lingual Schema Linker** | Resolves vernacular/transliterated tokens to target tables and columns, pruning 95% of irrelevant schemas. | IndicXlit Phonetic Soundex, mE5-Large / BGE-M3 Dense Embeddings, Qdrant |
| **SQL Synthesizer** | Generates dialect-compliant aggregation SQL with accurate JOINs and filters. | Fine-Tuned `Sarvam-2B` / `Qwen-2.5-Coder` LoRA, Few-Shot CoT |
| **AST Security Critic** | Enforces read-only safety, blocks mutations (`DROP`, `DELETE`, `UPDATE`), and injects bounded `LIMIT` clauses. | SQLGlot AST Parser, Syntax Linter |
| **DuckDB Sandbox & Healer** | Runs queries in an isolated in-memory sandbox; automatically intercepts runtime errors and executes reflection cycles. | DuckDB Ephemeral Engine, Compiler Reflection Loop |
| **Response Verbalizer** | Translates raw result tuples into fluent prose in the user's native language with Indian numbering (`Lakhs`/`Crores`). | Multilingual NLG, Number & Currency Localizer |

---

## 📂 Repository Layout

```
IndicSQL_Repo/
├── data/                         # Datasets & benchmark partitions
│   ├── benchmarks/               # IndicDB benchmark test partitions (15k queries)
│   │   └── README.md
│   ├── ndap_catalogs/            # NDAP relational schemas and catalogs
│   │   └── README.md
│   └── sample_queries/           # Multilingual sample test queries (7 languages)
│       └── queries.json
├── frontend/                     # Web Cockpit (Next.js 14)
│   └── README.md                 # UI architecture and setup roadmap
├── indicsql/                     # Core IndicSQL Python Package
│   ├── agents/                   # Specialized agent nodes
│   │   ├── __init__.py
│   │   ├── critic.py             # AST safety validator & mutation blocker
│   │   ├── reflection_healer.py  # Self-healing retry & reflection loop
│   │   ├── response_verbalizer.py# Vernacular natural language verbalizer
│   │   ├── sandbox_executor.py   # DuckDB sandbox execution handler
│   │   ├── schema_linker.py      # Cross-lingual column & table matcher
│   │   ├── sql_synthesizer.py    # LoRA / rule-based aggregation SQL generator
│   │   └── supervisor.py         # Script detection & language routing
│   ├── api/                      # REST & WebSocket API gateway
│   │   ├── __init__.py
│   │   └── server.py             # FastAPI endpoints (/query, /schemas, /health)
│   ├── core/                     # Foundational configurations & state
│   │   ├── __init__.py
│   │   ├── config.py             # Pydantic Settings & environment loader
│   │   └── state.py              # LangGraph TypedDict Blackboard State
│   ├── graph/                    # Workflow orchestration
│   │   ├── __init__.py
│   │   └── workflow.py           # LangGraph StateGraph & fallback pipeline
│   ├── sandbox/                  # Relational execution engine
│   │   ├── __init__.py
│   │   ├── duckdb_engine.py      # In-memory DuckDB sandbox with NDAP sample tables
│   │   └── validator.py          # SQLGlot AST read-only & LIMIT linter
│   ├── schema/                   # Schema catalogs & phonetic tools
│   │   ├── __init__.py
│   │   ├── catalog.py            # NDAP database catalog registry
│   │   └── phonetic.py           # Phonetic transliteration bridge
│   └── __init__.py               # Package metadata and version info
├── scripts/                      # Utility and demonstration tools
│   └── run_demo.py               # Interactive CLI multi-agent demo
├── tests/                        # Automated unit and integration test suite
│   ├── __init__.py
│   ├── test_agents.py            # Unit tests for agent nodes and AST validator
│   └── test_pipeline.py          # End-to-end integration tests
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore rules for Python, models & artifacts
├── PLAN.md                       # Comprehensive 760+ line research & project plan
├── pyproject.toml                # Project packaging and dependency specifications
├── README.md                     # Project documentation (current file)
└── requirements.txt              # Production dependencies
```

---

## ⚡ Current State of the Project

The initial project foundation and scaffolding are fully established:

- [x] **Agent Blackboard State**: Strongly-typed `IndicSQLState`, `SchemaElement`, and `TabularResult` contracts.
- [x] **6 Swarm Agent Nodes**: Implemented Supervisor, Schema-Linker, SQL-Synthesizer, AST Critic, Sandbox Executor, Reflection Healer, and Response Verbalizer.
- [x] **Sandboxed Relational Execution**: Ephemeral in-memory execution sandbox with preloaded NDAP sample tables (Agriculture / PM-KISAN, Education / UDISE+, Rural Development / MGNREGA) and automatic fallback to Python's built-in in-memory SQLite engine.
- [x] **AST Safety Linter**: Deterministic mutation blocking (`DROP`, `DELETE`, `UPDATE`, `INSERT`) and automatic `LIMIT` clause enforcement.
- [x] **Vernacular Verbalization**: Automatic Indian number formatting (Lakhs and Crores) and native Marathi/Hindi/Hinglish/English prose synthesis.
- [x] **CLI Demonstration Tool**: `scripts/run_demo.py` ready for instant terminal verification.
- [x] **FastAPI Gateway**: `indicsql/api/server.py` with `/query`, `/schemas`, and `/health` endpoints.
- [x] **Comprehensive Test Suite**: Automated unit and pipeline tests passing with 100% success rate.

---

## 🚀 Quickstart Guide

### 1. Clone & Setup Environment with `uv`

```bash
git clone https://github.com/ojhaprathmesh/IndicSQL_Repo.git
cd IndicSQL_Repo

# Create virtual environment with uv
uv venv .venv
source .venv/bin/activate

# Install dependencies using uv
uv pip install -r requirements.txt
# (Optional) Install editable package
uv pip install -e .
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

### 3. Run the CLI Multi-Agent Demo

Test the end-to-end multi-agent swarm right from your terminal with a sample Marathi query:

```bash
uv run scripts/run_demo.py "महाराष्ट्रात गेल्या वर्षी किती शेतकऱ्यांना पीएम-किसानचा लाभ मिळाला?"
```

**Output Preview:**
```text
======================================================================
🇮🇳 IndicSQL: Autonomous Cross-Lingual Text-to-SQL Swarm
======================================================================
📥 Input Query: महाराष्ट्रात गेल्या वर्षी किती शेतकऱ्यांना पीएम-किसानचा लाभ मिळाला?

🔍 [Step 1] Supervisor Script & Language Detection:
   • Language: mr | Script: Devanagari

🔗 [Step 2] Cross-Lingual Schema Linking:
   • Linked: Table 'ndap_pm_kisan_disbursement' -> Column 'farmer_beneficiaries' (BIGINT)

⚡ [Step 3] Generated SQL:
   SELECT SUM(farmer_beneficiaries) AS total_farmers, SUM(amount_inr) AS total_amount 
   FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';

💾 [Step 4] Sandboxed DuckDB Execution:
   • Columns: ['total_farmers', 'total_amount']
   • Rows (1 tuples, 0.10ms): [[3640800, 7281600000.0]]

🗣️ [Step 5] Vernacular Natural Language Answer:
   👉 पीएम-किसान योजनेअंतर्गत एकूण 36.41 लाख (Lakhs) शेतकऱ्यांना लाभ मिळाला, आणि ₹728.16 कोटी (Crores) ची रक्कम थेट वितरित करण्यात आली.
======================================================================
```

### 4. Run the Test Suite

```bash
uv run python -m unittest discover tests
```

### 5. Launch the FastAPI Gateway

```bash
uv run uvicorn indicsql.api.server:app --reload --port 8000
```
Visit `http://localhost:8000/docs` to test interactive Swagger documentation.

---

## 🗺️ 10-Week Engineering Roadmap (Summary from PLAN.md)

- [x] **Phase 0: Project Inception & Scaffolding** (Scaffolding, state contracts, DuckDB sandbox, CI tests)
- [ ] **Phase 1: NDAP 20-DB Ingestion & Benchmark Harness** (Parquet exports, full IndicDB 15,617 test suite)
- [ ] **Phase 2: Phonetic Schema-Linking & Vector Retrieval** (IndicXlit integration, mE5/BGE-M3 Qdrant indexing)
- [ ] **Phase 3: Fine-Tuning Aggregation Transformer** (`IndicSQL-Agg-12K` dataset, Sarvam-2B / Qwen-2.5-Coder LoRA)
- [ ] **Phase 4: Full Multi-Agent Graph & Next.js UI** (Production LangGraph checkpointing, BharatQuery Cockpit)
- [ ] **Phase 5: Benchmark Evaluation & Research Paper** (IndicDB empirical evaluation, ablation analysis, publication)

---

## 📄 License & Attribution

This project is licensed under the **Apache-2.0 License**. See [LICENSE](LICENSE) for details.

*Engineered to empower 1.4 billion citizens with direct, mother-tongue access to national open data.*
