#!/usr/bin/env python3
"""
CLI Demonstration of IndicSQL Swarm.
Runs end-to-end multi-agent pipeline for sample Indian language queries.
"""

import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from indicsql.graph.workflow import execute_indicsql_pipeline


def main():
    default_query = "महाराष्ट्रात गेल्या वर्षी किती शेतकऱ्यांना पीएम-किसानचा लाभ मिळाला?"
    query = sys.argv[1] if len(sys.argv) > 1 else default_query

    print("=" * 70)
    print("🇮🇳 IndicSQL: Autonomous Cross-Lingual Text-to-SQL Swarm")
    print("=" * 70)
    print(f"📥 Input Query: {query}\n")

    state = execute_indicsql_pipeline(query)

    print("🔍 [Step 1] Supervisor Script & Language Detection:")
    print(f"   • Language: {state.get('detected_lang')} | Script: {state.get('detected_script')}")

    print("\n🔗 [Step 2] Cross-Lingual Schema Linking:")
    for elem in state.get("pruned_schema", []):
        print(f"   • Linked: Table '{elem['table_name']}' -> Column '{elem['column_name']}' ({elem['data_type']})")

    print("\n⚡ [Step 3] Generated SQL:")
    print(f"   {state.get('generated_sql')}")

    print("\n💾 [Step 4] Sandboxed DuckDB Execution:")
    res = state.get("execution_result")
    if res:
        print(f"   • Columns: {res.get('columns')}")
        print(f"   • Rows ({res.get('row_count')} tuples, {res.get('execution_time_ms', 0):.2f}ms): {res.get('rows')}")
    else:
        print(f"   • Error: {state.get('execution_error')}")

    print("\n🗣️ [Step 5] Vernacular Natural Language Answer:")
    print(f"   👉 {state.get('verbalized_response')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
