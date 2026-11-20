/**
 * Strongly-typed API Contracts for BharatQuery / IndicSQL Backend.
 */

export interface ExecutionResult {
  columns: string[];
  rows: (string | number | boolean | null)[][];
  row_count?: number;
  execution_time_ms?: number;
}

export interface AuditStep {
  step: number;
  agent: string;
  action: string;
  matched_table?: string;
  matched_columns?: string[];
  confidence?: number;
  is_safe?: boolean;
  status?: "success" | "error";
  error?: string;
  execution_time_ms?: number;
  row_count?: number;
  [key: string]: unknown;
}

export interface QueryResponse {
  query_id: string;
  raw_query: string;
  detected_language: string;
  detected_script: string;
  generated_sql: string;
  raw_stochastic_sql?: string;
  verbalized_response: string;
  execution_result: ExecutionResult | null;
  audit_trace?: AuditStep[];
}

export interface QueryRequest {
  query: string;
  language?: "en" | "hi" | "hi-en" | "mr" | "bn" | "ta" | "te";
  session_id?: string;
}

export interface BackendHealthResponse {
  status: string;
}

export interface RootServiceResponse {
  service: string;
  version: string;
  status: string;
  supported_languages: string[];
}

export interface VoiceTranscribeResponse {
  transcript: string;
  detected_language: string;
  raw_response?: Record<string, unknown>;
}

export interface VoiceSynthesizeRequest {
  text: string;
  language_code?: string;
  speaker?: string;
}

export interface VoiceSynthesizeResponse {
  audio_base64?: string;
  target_language_code?: string;
  speaker?: string;
}

export interface ColumnMetadata {
  name: string;
  type: string;
  nullable?: boolean;
  description?: string;
}

export interface TableMetadata {
  table_name: string;
  domain?: string;
  description?: string;
  row_count?: number;
  columns?: ColumnMetadata[] | Record<string, string>;
}

export interface SchemasResponse {
  count: number;
  tables: Record<string, TableMetadata>;
}

export interface BenchmarkLanguageMetrics {
  total_queries: number;
  grounding_accuracy_pct: number;
  table_routing_accuracy_pct: number;
  execution_accuracy_pct: number;
  verbalization_accuracy_pct: number;
  avg_latency_ms: number;
  failures: unknown[];
}

export interface ProjectAnalytics {
  benchmark: {
    timestamp: string;
    total_queries: number;
    overall_metrics: {
      grounding_accuracy_pct: number;
      table_routing_accuracy_pct: number;
      execution_accuracy_pct: number;
      verbalization_accuracy_pct: number;
      avg_latency_ms: number;
      total_benchmark_seconds: number;
    };
    language_scorecards: Record<string, BenchmarkLanguageMetrics>;
  };
  models: {
    benchmark_metadata: {
      benchmark_name: string;
      release_date: string;
      databases_covered: number;
      languages: string[];
    };
    models: Record<
      string,
      {
        model_name: string;
        provider: string;
        model_type: string;
        parameter_size: string;
        execution_accuracy_pct: Record<string, number>;
        indic_avg_ex_pct: number;
        indic_to_english_gap_delta_pct: number;
        schema_f1: number;
        avg_latency_ms: number;
        cost_per_1k_queries_usd: number;
      }
    >;
  };
  failures: {
    total_audited_failures: number;
    benchmark_summary: {
      total_queries: number;
      passed_queries: number;
      failed_queries: number;
      execution_accuracy_pct: number;
      grounding_accuracy_pct: number;
      table_routing_accuracy_pct: number;
      verbalization_accuracy_pct: number;
    };
    failure_category_counts: Record<string, number>;
    traces: FailureTrace[];
  };
  benchmark_queries: BenchmarkQuery[];
}

export interface FailureTrace {
  query_id: string;
  original_question: string;
  language_detected: string;
  selected_table: string;
  generated_sql: string;
  exact_failure_reason: string;
  primary_category: string;
}

export interface BenchmarkQuery {
  query_id: string;
  query: string;
  language: string;
  script: string;
  domain: string;
  target_table: string;
  gold_sql: string;
  difficulty: string;
  target_columns: string[];
}

export interface SqlInspectResponse {
  valid: boolean;
  sql: string;
  message: string;
  execution_result: ExecutionResult | null;
}

export interface StoredQuery {
  id: string;
  question: string;
  createdAt: string;
  language?: string;
  status: "success" | "failure";
  response?: QueryResponse;
  error?: string;
}
