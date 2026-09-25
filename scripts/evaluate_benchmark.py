#!/usr/bin/env python3
"""
CLI Benchmark Runner for IndicDB Evaluation Suite (Phase 1: p1_2).
Usage:
    uv run scripts/evaluate_benchmark.py [--output results.json]
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tabulate import tabulate  # noqa: E402

from indicsql.benchmark.dataset import load_benchmark_dataset  # noqa: E402
from indicsql.benchmark.evaluator import IndicDBEvaluator  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="IndicDB Text-to-SQL Benchmark Evaluation Harness")
    parser.add_argument("--suite", type=str, default=None, help="Path to custom benchmark suite JSON file")
    parser.add_argument("--save", action="store_true", default=True, help="Save evaluation artifacts to disk")
    args = parser.parse_args()

    suite_path = Path(args.suite) if args.suite else None
    queries = load_benchmark_dataset(suite_path)

    print("=" * 80)
    print("🇮🇳 IndicSQL: IndicDB Benchmark Evaluation Harness (April 2026)")
    print("=" * 80)
    print(f"Loaded {len(queries)} evaluation questions across 7 languages & 20 NDAP databases.\n")

    evaluator = IndicDBEvaluator()
    report = evaluator.evaluate_suite(queries, save_results=args.save)

    # Format per-language summary table
    headers = ["Language", "Code", "Queries", "Execution Acc (EX)", "Schema F1", "Avg Latency (ms)"]
    lang_names = {
        "en": "English (Baseline)",
        "hi-en": "Hinglish (Code-Mixed)",
        "mr": "Marathi",
        "hi": "Hindi",
        "bn": "Bengali",
        "ta": "Tamil",
        "te": "Telugu",
    }
    table_rows = []
    for code, m in report["per_language_metrics"].items():
        name = lang_names.get(code, code)
        table_rows.append([
            name,
            code,
            m["total_queries"],
            f"{m['execution_accuracy_pct']:.1f}%",
            f"{m['schema_f1']:.3f}",
            f"{m['avg_latency_ms']:.1f}ms",
        ])

    print("\n" + "=" * 80)
    print("📋 BENCHMARK PERFORMANCE MATRIX (EX & SCHEMA F1)")
    print("=" * 80)
    print(tabulate(table_rows, headers=headers, tablefmt="github"))

    print("\n📈 SUMMARY BENCHMARK METRICS:")
    print(f"   • Overall Execution Accuracy:  {report['overall_execution_accuracy_pct']}%")
    print(f"   • English Baseline Accuracy:   {report['english_accuracy_pct']}%")
    print(f"   • Average Indic Accuracy:      {report['average_indic_accuracy_pct']}%")
    delta = report['indic_to_english_gap_delta_pct']
    delta_color = "🟢 Target Parity Achieved" if delta <= 2.0 else "🟡 Gap Pending Fine-Tuning"
    print(f"   • Indic-to-English Gap Delta:  {delta}% ({delta_color})")
    print("=" * 80)


if __name__ == "__main__":
    main()
