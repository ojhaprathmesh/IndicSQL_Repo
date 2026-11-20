"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowUpRight,
  CheckCircle2,
  Code2,
  ExternalLink,
  LoaderCircle,
  RefreshCw,
  Search,
  ShieldCheck,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ExecutionPipeline } from "@/components/results/ExecutionPipeline";
import { DataTable } from "@/components/results/DataTable";
import { SqlViewer } from "@/components/results/SqlViewer";
import { Button } from "@/components/ui/Button";
import { apiClient } from "@/lib/api-client";
import { formatLatency } from "@/lib/formatters";
import {
  BenchmarkQuery,
  ProjectAnalytics,
  SqlInspectResponse,
  StoredQuery,
} from "@/types/api";

interface WorkspaceModuleProps {
  module: string;
  history: StoredQuery[];
  schemasCount: number;
  onReuseQuery: (record: StoredQuery) => void;
}

const LANGUAGE_NAMES: Record<string, string> = {
  en: "English",
  "hi-en": "Hinglish",
  hi: "Hindi",
  mr: "Marathi",
  bn: "Bengali",
  ta: "Tamil",
  te: "Telugu",
};

const number = (value?: number, suffix = "") =>
  value === undefined || !Number.isFinite(value)
    ? "Not available"
    : `${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}${suffix}`;

function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{value}</p>
      <p className="mt-1 text-[11px] leading-5 text-slate-500">{detail}</p>
    </div>
  );
}

function Panel({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
        {description && <p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>}
      </div>
      {children}
    </section>
  );
}

function QueryHistory({
  history,
  onReuse,
}: {
  history: StoredQuery[];
  onReuse: (record: StoredQuery) => void;
}) {
  const [search, setSearch] = useState("");
  const [language, setLanguage] = useState("all");
  const [status, setStatus] = useState("all");
  const languages = useMemo(
    () => Array.from(new Set(history.map((record) => record.language).filter(Boolean))) as string[],
    [history]
  );
  const filtered = history.filter((record) => {
    const textMatch = record.question.toLowerCase().includes(search.toLowerCase());
    const languageMatch = language === "all" || record.language === language;
    const statusMatch = status === "all" || record.status === status;
    return textMatch && languageMatch && statusMatch;
  });

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-[1fr_180px_150px]">
        <label className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search past questions"
            className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-slate-800 outline-none focus:border-violet-500"
          />
        </label>
        <select
          value={language}
          onChange={(event) => setLanguage(event.target.value)}
          className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
          aria-label="Filter by language"
        >
          <option value="all">All languages</option>
          {languages.map((code) => (
            <option key={code} value={code}>{LANGUAGE_NAMES[code] || code}</option>
          ))}
        </select>
        <select
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
          aria-label="Filter by status"
        >
          <option value="all">All statuses</option>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
        </select>
      </div>
      {filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 py-12 text-center text-sm text-slate-500">
          {history.length ? "No queries match these filters." : "Your completed queries will be saved here in this browser."}
        </div>
      ) : (
        <div className="divide-y divide-slate-100 rounded-xl border border-slate-200">
          {filtered.map((record) => (
            <article key={record.id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <p className="line-clamp-2 text-sm font-medium text-slate-900">{record.question}</p>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                  <span>{new Date(record.createdAt).toLocaleString()}</span>
                  {record.language && <span>· {LANGUAGE_NAMES[record.language] || record.language}</span>}
                  <span>· {record.status}</span>
                  {record.response?.execution_result && (
                    <span>· {record.response.execution_result.row_count ?? record.response.execution_result.rows.length} rows</span>
                  )}
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={() => onReuse(record)} className="shrink-0">
                <RefreshCw className="h-3.5 w-3.5" /> Reuse
              </Button>
            </article>
          ))}
        </div>
      )}
      <p className="text-[11px] text-slate-400">History is stored in this browser only; it is not synchronized to the backend or other devices.</p>
    </div>
  );
}

function SqlInspector({ initialSql }: { initialSql: string }) {
  const [sql, setSql] = useState(initialSql);
  const [result, setResult] = useState<SqlInspectResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inspect = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await apiClient.inspectSql(sql));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "SQL inspection failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="sql-inspector-editor" className="mb-2 block text-xs font-medium text-slate-600">DuckDB SQL</label>
        <textarea
          id="sql-inspector-editor"
          value={sql}
          onChange={(event) => setSql(event.target.value)}
          spellCheck={false}
          rows={9}
          placeholder="SELECT state_name, SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement GROUP BY state_name;"
          className="w-full rounded-xl border border-slate-700 bg-slate-950 p-4 font-mono text-sm leading-6 text-emerald-200 outline-none focus:ring-2 focus:ring-violet-500"
        />
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-500">Only read-only SELECT/WITH queries are accepted; results are capped at 1,000 rows.</p>
        <div className="flex flex-wrap gap-2">
          <Button onClick={inspect} disabled={!sql.trim() || isLoading}>
            {isLoading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
            Validate &amp; execute
          </Button>
        </div>
      </div>
      {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>}
      {result && (
        <div className={`rounded-xl border p-4 ${result.valid ? "border-emerald-200 bg-emerald-50" : "border-rose-200 bg-rose-50"}`}>
          <div className="flex items-center gap-2 text-sm font-semibold">
            {result.valid ? <CheckCircle2 className="h-4 w-4 text-emerald-700" /> : <AlertCircle className="h-4 w-4 text-rose-700" />}
            <span className={result.valid ? "text-emerald-900" : "text-rose-900"}>{result.message}</span>
          </div>
          {result.sql !== sql && <p className="mt-2 text-xs text-slate-600">The backend added a safety limit to the executed SQL.</p>}
          {result.valid && result.execution_result && (
            <>
              <div className="mt-4 flex flex-wrap gap-4 text-xs text-slate-600">
                <span>{result.execution_result.row_count} rows</span>
                <span>{formatLatency(result.execution_result.execution_time_ms)}</span>
              </div>
              <div className="mt-4">
                <DataTable columns={result.execution_result.columns} rows={result.execution_result.rows} />
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function LoadingPanel({ error, retry }: { error: string | null; retry: () => void }) {
  if (error) {
    return (
      <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-800">
        <p className="font-semibold">Could not load project evaluation artifacts</p>
        <p className="mt-1">{error}</p>
        <Button variant="outline" size="sm" className="mt-4" onClick={retry}><RefreshCw className="h-4 w-4" /> Retry</Button>
      </div>
    );
  }
  return <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500"><LoaderCircle className="h-4 w-4 animate-spin" /> Loading checked-in evaluation data…</div>;
}

function ScoreDashboard({
  analytics,
  mode,
}: {
  analytics: ProjectAnalytics;
  mode: "overview" | "benchmark-dashboard" | "language-analytics" | "model-comparison";
}) {
  const scorecards = analytics.benchmark.language_scorecards;
  const languageData = Object.entries(scorecards).map(([code, metrics]) => ({
    language: LANGUAGE_NAMES[code] || code,
    accuracy: metrics.execution_accuracy_pct,
    latency: metrics.avg_latency_ms,
    queries: metrics.total_queries,
  }));
  const benchmarkMetrics = analytics.benchmark.overall_metrics;
  const models = Object.entries(analytics.models.models).map(([id, model]) => ({
    id,
    name: model.model_name,
    accuracy: model.execution_accuracy_pct.overall,
    latency: model.avg_latency_ms,
    schema: model.schema_f1 * 100,
    gap: model.indic_to_english_gap_delta_pct,
  }));

  return (
    <div className="space-y-6">
      {mode !== "model-comparison" ? (
        <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Evaluated queries" value={number(analytics.benchmark.total_queries)} detail="Unseen 140-query evaluation report" />
            <MetricCard label="Execution accuracy" value={number(benchmarkMetrics.execution_accuracy_pct, "%")} detail={`Grounding ${number(benchmarkMetrics.grounding_accuracy_pct, "%")} · Routing ${number(benchmarkMetrics.table_routing_accuracy_pct, "%")}`} />
            <MetricCard label="Average latency" value={formatLatency(benchmarkMetrics.avg_latency_ms)} detail="End-to-end evaluation average" />
            <MetricCard label="Languages" value={String(Object.keys(scorecards).length)} detail="English, Hinglish, Hindi, Marathi, Bengali, Tamil, Telugu" />
          </div>
          <div className="grid gap-5 xl:grid-cols-2">
            <Panel title="Execution accuracy by language" description="Values from the checked-in unseen evaluation report.">
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={languageData} margin={{ top: 8, right: 12, left: -20, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="language" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="accuracy" name="Execution accuracy %" fill="#7c3aed" radius={[5, 5, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Panel>
            <Panel title="Latency by language" description="Measured milliseconds in the same evaluation report.">
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={languageData} margin={{ top: 8, right: 12, left: -20, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="language" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="latency" name="Latency ms" stroke="#0f766e" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Panel>
          </div>
          {mode === "overview" && (
            <Panel title="Engineering evaluation" description={`Evaluation snapshot: ${analytics.benchmark.timestamp || "date not recorded"}`}>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard label="Schema grounding" value={number(benchmarkMetrics.grounding_accuracy_pct, "%")} detail="Grounding accuracy" />
                <MetricCard label="Table routing" value={number(benchmarkMetrics.table_routing_accuracy_pct, "%")} detail="Correct target-table routing" />
                <MetricCard label="Verbalization" value={number(benchmarkMetrics.verbalization_accuracy_pct, "%")} detail="Evaluation report score" />
                <MetricCard label="Benchmark duration" value={`${number(benchmarkMetrics.total_benchmark_seconds)} s`} detail="Total reported benchmark runtime" />
              </div>
              <p className="mt-4 text-[11px] text-slate-400">These are stored evaluation results, not live production telemetry.</p>
            </Panel>
          )}
          {mode === "language-analytics" && (
            <Panel title="Language scorecard" description="Per-language query counts, scores, and average latency.">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead><tr className="border-b border-slate-200 text-slate-500"><th className="py-2 pr-4">Language</th><th className="py-2 pr-4">Queries</th><th className="py-2 pr-4">Execution accuracy</th><th className="py-2 pr-4">Grounding</th><th className="py-2">Latency</th></tr></thead>
                  <tbody>{Object.entries(scorecards).map(([code, item]) => <tr key={code} className="border-b border-slate-100 text-slate-700"><td className="py-3 pr-4 font-medium">{LANGUAGE_NAMES[code] || code}</td><td className="py-3 pr-4">{item.total_queries}</td><td className="py-3 pr-4">{number(item.execution_accuracy_pct, "%")}</td><td className="py-3 pr-4">{number(item.grounding_accuracy_pct, "%")}</td><td className="py-3">{formatLatency(item.avg_latency_ms)}</td></tr>)}</tbody>
                </table>
              </div>
            </Panel>
          )}
        </>
      ) : (
        <>
          <Panel title="Model comparison" description={`Recorded baseline matrix · ${analytics.models.benchmark_metadata.benchmark_name}`}>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-xs">
                <thead><tr className="border-b border-slate-200 text-slate-500"><th className="py-2 pr-4">Model</th><th className="py-2 pr-4">Execution accuracy</th><th className="py-2 pr-4">Schema F1</th><th className="py-2 pr-4">Avg. latency</th><th className="py-2">Indic-English gap</th></tr></thead>
                <tbody>{models.map((model) => <tr key={model.id} className="border-b border-slate-100 text-slate-700"><td className="max-w-[360px] py-3 pr-4 font-medium text-slate-900">{model.name}</td><td className="py-3 pr-4">{number(model.accuracy, "%")}</td><td className="py-3 pr-4">{number(model.schema, "%")}</td><td className="py-3 pr-4">{formatLatency(model.latency)}</td><td className="py-3">{number(model.gap, "%")}</td></tr>)}</tbody>
              </table>
            </div>
          </Panel>
          <Panel title="Model execution accuracy" description="Overall benchmark accuracy, as recorded in baseline_models_matrix.json.">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={models} layout="vertical" margin={{ top: 8, right: 20, left: 30, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" width={210} tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="accuracy" name="Execution accuracy %" fill="#4f46e5" radius={[0, 5, 5, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        </>
      )}
      <p className="text-[11px] leading-5 text-slate-400">
        Source files: <code>data/benchmarks/unseen_140_evaluation_report.json</code> and{" "}
        <code>data/benchmarks/baseline_models_matrix.json</code>. Results may describe different benchmark runs; they are not merged into a synthetic score.
      </p>
    </div>
  );
}

function FailureAnalysis({ analytics }: { analytics: ProjectAnalytics }) {
  const [category, setCategory] = useState("all");
  const [language, setLanguage] = useState("all");
  const audit = analytics.failures;
  const traces = audit.traces.filter(
    (trace) =>
      (category === "all" || trace.primary_category === category) &&
      (language === "all" || trace.language_detected === language)
  );

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Audited failures" value={number(audit.total_audited_failures)} detail={`${audit.benchmark_summary.failed_queries} failures in this audit`} />
        <MetricCard label="Audit execution accuracy" value={number(audit.benchmark_summary.execution_accuracy_pct, "%")} detail={`${audit.benchmark_summary.passed_queries} of ${audit.benchmark_summary.total_queries} passed`} />
        <MetricCard label="Grounding accuracy" value={number(audit.benchmark_summary.grounding_accuracy_pct, "%")} detail="This failure audit's own summary" />
        <MetricCard label="Failure categories" value={String(Object.keys(audit.failure_category_counts).length)} detail="Categorized from audited traces" />
      </div>
      <Panel title="Failure categories" description="Counts in reports/e2e_failure_audit.json.">
        <div className="space-y-3">
          {Object.entries(audit.failure_category_counts).map(([name, count]) => {
            const percent = audit.total_audited_failures ? count / audit.total_audited_failures * 100 : 0;
            return <div key={name}><div className="mb-1 flex justify-between text-xs text-slate-700"><span>{name}</span><span>{count}</span></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-violet-600" style={{ width: `${percent}%` }} /></div></div>;
          })}
        </div>
      </Panel>
      <Panel title="Audited failure traces" description={`${traces.length} matching trace(s). Failure explanations are quoted from the repository audit.`}>
        <div className="mb-4 grid gap-3 sm:grid-cols-2">
          <select value={category} onChange={(event) => setCategory(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700" aria-label="Filter failures by category"><option value="all">All categories</option>{Object.keys(audit.failure_category_counts).map((item) => <option key={item}>{item}</option>)}</select>
          <select value={language} onChange={(event) => setLanguage(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700" aria-label="Filter failures by language"><option value="all">All languages</option>{Array.from(new Set(audit.traces.map((item) => item.language_detected))).map((item) => <option key={item} value={item}>{LANGUAGE_NAMES[item] || item}</option>)}</select>
        </div>
        <div className="space-y-3">
          {traces.map((trace) => <details key={trace.query_id} className="rounded-xl border border-slate-200 p-4"><summary className="cursor-pointer text-sm font-medium text-slate-900">{trace.original_question}<span className="ml-2 text-[11px] font-normal text-slate-500">· {trace.primary_category} · {LANGUAGE_NAMES[trace.language_detected] || trace.language_detected}</span></summary><div className="mt-4 space-y-3 text-xs"><p><strong>Table:</strong> {trace.selected_table}</p><p className="leading-5 text-slate-600"><strong>Audit finding:</strong> {trace.exact_failure_reason}</p><SqlViewer sql={trace.generated_sql} /></div></details>)}
          {traces.length === 0 && <p className="py-8 text-center text-sm text-slate-500">No audited traces match the selected filters.</p>}
        </div>
      </Panel>
      <p className="text-[11px] text-slate-400">This 140-query audit is a distinct evaluation artifact from the unseen benchmark report. The two summaries are intentionally shown separately.</p>
    </div>
  );
}

function BenchmarkExplorer({ queries }: { queries: BenchmarkQuery[] }) {
  const [search, setSearch] = useState("");
  const [language, setLanguage] = useState("all");
  const [domain, setDomain] = useState("all");
  const [selected, setSelected] = useState<BenchmarkQuery | null>(null);
  const domains = Array.from(new Set(queries.map((query) => query.domain)));
  const languages = Array.from(new Set(queries.map((query) => query.language)));
  const visible = queries.filter((query) =>
    (language === "all" || query.language === language) &&
    (domain === "all" || query.domain === domain) &&
    `${query.query_id} ${query.query} ${query.target_table}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-[1fr_180px_200px]">
        <label className="relative"><Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search query, table, or ID" className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-slate-800" /></label>
        <select value={language} onChange={(event) => setLanguage(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"><option value="all">All languages</option>{languages.map((item) => <option key={item} value={item}>{LANGUAGE_NAMES[item] || item}</option>)}</select>
        <select value={domain} onChange={(event) => setDomain(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"><option value="all">All domains</option>{domains.map((item) => <option key={item}>{item}</option>)}</select>
      </div>
      <div className="text-xs text-slate-500">Showing {visible.length} of {queries.length} benchmark questions. SQL is the checked-in gold reference, not generated output.</div>
      <div className="space-y-2">{visible.map((item) => <article key={item.query_id} className="rounded-xl border border-slate-200 bg-white p-4"><div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-500"><span className="font-mono">{item.query_id}</span><span>· {LANGUAGE_NAMES[item.language] || item.language}</span><span>· {item.domain}</span><span>· {item.difficulty}</span></div><p className="mt-2 text-sm font-medium text-slate-900">{item.query}</p><p className="mt-1 text-xs text-slate-500">Table: <code>{item.target_table}</code></p><button type="button" onClick={() => setSelected(selected?.query_id === item.query_id ? null : item)} className="mt-2 text-xs font-semibold text-violet-700">{selected?.query_id === item.query_id ? "Hide gold SQL" : "View gold SQL"}</button>{selected?.query_id === item.query_id && <div className="mt-3"><SqlViewer sql={item.gold_sql} /></div>}</article>)}</div>
    </div>
  );
}

export function WorkspaceModule({
  module,
  history,
  schemasCount,
  onReuseQuery,
}: WorkspaceModuleProps) {
  const [analytics, setAnalytics] = useState<ProjectAnalytics | null>(null);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const latestSql = history.find((record) => record.response?.generated_sql)?.response?.generated_sql || "";
  const needsAnalytics = [
    "overview",
    "benchmark-dashboard",
    "benchmark-explorer",
    "language-analytics",
    "model-comparison",
    "failure-analysis",
  ].includes(module);

  const loadAnalytics = async () => {
    setIsLoading(true);
    setAnalyticsError(null);
    try {
      setAnalytics(await apiClient.fetchAnalytics());
    } catch (error) {
      setAnalyticsError(error instanceof Error ? error.message : "Analytics could not be loaded.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (needsAnalytics) void loadAnalytics();
    // Load once when a data-backed module is opened.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [module]);

  if (module === "query-history") return <QueryHistory history={history} onReuse={onReuseQuery} />;
  if (["sql-quality", "sql-inspector", "ai-reviewer"].includes(module)) {
    return (
      <div className="space-y-5">
        {module === "ai-reviewer" && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-900">
            This performs the backend AST safety check and sandbox execution. It does not call an LLM for semantic code review, so it cannot assess business intent or guarantee query correctness.
          </div>
        )}
        {module === "sql-quality" && (
          <div className="rounded-xl border border-violet-200 bg-violet-50 p-4 text-xs leading-5 text-violet-900">
            Quality signals are limited to read-only AST validation and actual sandbox execution. Schema/intent correctness requires comparing the result with your intended question.
          </div>
        )}
        <SqlInspector initialSql={latestSql} />
        {latestSql && module === "sql-quality" && <Panel title="Latest generated query"><SqlViewer sql={latestSql} /></Panel>}
      </div>
    );
  }

  if (module === "pipeline-explorer") {
    const traced = history.filter((record) => record.response);
    return <div className="space-y-4">{traced.length ? traced.map((record) => <Panel key={record.id} title={record.question} description={`${new Date(record.createdAt).toLocaleString()} · ${record.response?.query_id}`}><ExecutionPipeline data={record.response!} /></Panel>) : <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">Run a query in AI Chat to see its real pipeline trace here.</div>}</div>;
  }

  if (needsAnalytics && !analytics) return <LoadingPanel error={analyticsError} retry={() => void loadAnalytics()} />;
  if (!analytics && module !== "research" && module !== "about" && module !== "dataset-explorer" && module !== "schema-explorer") {
    return <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">This workspace view is unavailable.</div>;
  }

  if (module === "overview") return <ScoreDashboard analytics={analytics!} mode="overview" />;
  if (module === "benchmark-dashboard") return <ScoreDashboard analytics={analytics!} mode="benchmark-dashboard" />;
  if (module === "language-analytics") return <ScoreDashboard analytics={analytics!} mode="language-analytics" />;
  if (module === "model-comparison") return <ScoreDashboard analytics={analytics!} mode="model-comparison" />;
  if (module === "failure-analysis") return <FailureAnalysis analytics={analytics!} />;
  if (module === "benchmark-explorer") return <BenchmarkExplorer queries={analytics!.benchmark_queries} />;
  if (module === "dataset-explorer" || module === "schema-explorer") {
    return <div className="rounded-xl border border-slate-200 bg-white p-5"><p className="text-sm font-semibold text-slate-900">{schemasCount} live tables available</p><p className="mt-1 text-xs text-slate-500">Open the live schema catalog to search datasets and inspect their columns and metadata.</p><Button variant="outline" size="sm" className="mt-4" onClick={() => window.dispatchEvent(new CustomEvent("indicsql:open-schemas"))}><ArrowUpRight className="h-4 w-4" /> Open schema catalog</Button></div>;
  }
  if (module === "research" || module === "about") {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Project overview"><p className="text-sm leading-6 text-slate-600">IndicSQL is a multilingual natural-language-to-SQL research platform for querying NDAP-style public datasets. It connects a query-language supervisor, cross-lingual schema linker, SQL synthesizer, AST safety critic, DuckDB sandbox, and response verbalizer.</p></Panel>
        <Panel title="Supported languages"><p className="text-sm leading-6 text-slate-600">English, Hindi, Hinglish, Bengali, Tamil, Telugu, and Marathi. The backend detects language from the submitted query.</p></Panel>
        <Panel title="Technology stack"><p className="text-sm leading-6 text-slate-600">Frontend: Next.js, React, TypeScript, Tailwind CSS, and Recharts. Backend: Python, FastAPI, LangGraph pipeline components, SQLGlot validation, and DuckDB.</p></Panel>
        <Panel title="Datasets & evaluation"><p className="text-sm leading-6 text-slate-600">The checked-in catalog covers 20 NDAP-style tables. Evaluation dashboards use the repository's unseen-query report, model baseline matrix, benchmark suite, and audited-failure report.</p></Panel>
        <Panel title="Architecture & limitations"><p className="text-sm leading-6 text-slate-600">The browser calls the FastAPI service directly. Queries execute in a read-only, bounded DuckDB sandbox. Query history stays in the current browser. AI semantic SQL review and cross-device history sync are not provided by the current model/API integration.</p></Panel>
        <Panel title="Project resources"><div className="space-y-3 text-sm"><a className="flex items-center gap-2 font-medium text-violet-700 hover:text-violet-900" href="https://github.com/JHANKARBANSAL/INDIC_LANGUAGE" target="_blank" rel="noreferrer">Repository and documentation <ExternalLink className="h-4 w-4" /></a><p className="text-xs leading-5 text-slate-500">Read README.md, PLAN.md, reports/e2e_failure_audit.md, and data/benchmarks/README.md for implementation notes and research context.</p></div></Panel>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">
      <div className="flex items-center gap-2"><Code2 className="h-4 w-4 text-violet-700" />Module content is not available.</div>
      <a className="mt-3 inline-flex items-center gap-1 text-violet-700" href="https://github.com/JHANKARBANSAL/INDIC_LANGUAGE" target="_blank" rel="noreferrer">Project repository <ExternalLink className="h-3.5 w-3.5" /></a>
    </div>
  );
}
