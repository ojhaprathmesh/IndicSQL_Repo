"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  ArrowDown,
  Database,
  LoaderCircle,
  MessageSquareText,
  Sparkles,
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { DatabaseDrawer } from "@/components/layout/DatabaseDrawer";
import { QueryComposer } from "@/components/query/QueryComposer";
import { SampleQuestions } from "@/components/query/SampleQuestions";
import { ResultsWorkspace } from "@/components/results/ResultsWorkspace";
import { Button } from "@/components/ui/Button";
import { apiClient, ApiError } from "@/lib/api-client";
import { QueryResponse, SchemasResponse } from "@/types/api";

interface ConversationTurn {
  id: string;
  question: string;
  response?: QueryResponse;
  error?: string;
  isLoading: boolean;
}

const MODULE_TITLES: Record<string, string> = {
  overview: "Overview",
  "query-history": "Query History",
  "sql-quality": "SQL Quality Inspector",
  "ai-reviewer": "AI SQL Reviewer",
  "sql-inspector": "SQL Inspector",
  "pipeline-explorer": "Query Pipeline Explorer",
  "benchmark-dashboard": "Benchmark Dashboard",
  "benchmark-explorer": "Benchmark Explorer",
  "language-analytics": "Language Analytics",
  "model-comparison": "Model Comparison",
  "failure-analysis": "Failure Analysis",
  "dataset-explorer": "Dataset Explorer",
  "schema-explorer": "Schema Explorer",
  research: "Research & Documentation",
  about: "About IndicSQL",
};

const MODULE_DESCRIPTIONS: Record<string, string> = {
  overview: "Project-wide metrics and evaluation charts are not exposed by the current API.",
  "query-history": "The current backend does not provide a query-history endpoint or persistent query store.",
  "sql-quality": "The backend validates generated SQL inside the query pipeline, but does not expose a standalone SQL review endpoint.",
  "ai-reviewer": "No standalone AI SQL reviewer endpoint is available in the current backend.",
  "sql-inspector": "The existing API returns generated SQL as part of a live query response. Paste-and-inspect is not currently supported.",
  "pipeline-explorer": "Pipeline trace details are available for queries run in AI Chat. Historical traces are not stored by the current API.",
  "benchmark-dashboard": "Benchmark metrics are available as repository evaluation artifacts, but the backend does not expose them as an API.",
  "benchmark-explorer": "The current backend does not expose benchmark query browsing or filtering endpoints.",
  "language-analytics": "The current backend does not expose per-language live evaluation metrics.",
  "model-comparison": "Model evaluation artifacts exist in the repository, but no model comparison API is available.",
  "failure-analysis": "The backend does not expose an aggregated failure-analysis endpoint.",
  research: "Project architecture, datasets, and development notes are documented in the repository README and documentation.",
  about: "IndicSQL is a multilingual text-to-SQL project for exploring NDAP public data using seven supported languages.",
};

export default function Home() {
  const [query, setQuery] = useState("");
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [backendStatus, setBackendStatus] = useState<
    "connected" | "disconnected" | "checking"
  >("checking");
  const [schemas, setSchemas] = useState<SchemasResponse | null>(null);
  const [isLoadingSchemas, setIsLoadingSchemas] = useState(false);
  const [schemasError, setSchemasError] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [activeModule, setActiveModule] = useState("chat");
  const [isAtBottom, setIsAtBottom] = useState(true);
  const abortControllerRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isMounted = true;

    async function initBackend() {
      try {
        await apiClient.checkHealth();
        if (!isMounted) return;
        setBackendStatus("connected");
      } catch {
        if (isMounted) setBackendStatus("disconnected");
        return;
      }

      if (!isMounted) return;
      setIsLoadingSchemas(true);
      try {
        const schemaData = await apiClient.fetchSchemas();
        if (isMounted) setSchemas(schemaData);
      } catch (error) {
        if (isMounted) {
          setSchemasError(
            error instanceof Error ? error.message : "Could not load the schema catalog."
          );
        }
      } finally {
        if (isMounted) setIsLoadingSchemas(false);
      }
    }

    void initBackend();
    return () => {
      isMounted = false;
      abortControllerRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (isAtBottom) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, isAtBottom]);

  const handleQuerySubmit = async (submittedQuery: string) => {
    const question = submittedQuery.trim();
    if (!question) return;
    abortControllerRef.current?.abort();

    const controller = new AbortController();
    abortControllerRef.current = controller;
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setActiveModule("chat");
    setQuery("");
    setTurns((current) => [
      ...current,
      { id, question, isLoading: true },
    ]);

    try {
      const response = await apiClient.submitQuery(question, controller.signal);
      setTurns((current) =>
        current.map((turn) =>
          turn.id === id ? { ...turn, response, isLoading: false } : turn
        )
      );
      setBackendStatus("connected");
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      const message =
        error instanceof ApiError
          ? error.message
          : "An unexpected error occurred while processing your query.";
      setTurns((current) =>
        current.map((turn) =>
          turn.id === id ? { ...turn, error: message, isLoading: false } : turn
        )
      );
      if (error instanceof ApiError && error.status === 0) {
        setBackendStatus("disconnected");
      }
    }
  };

  const startNewConversation = () => {
    abortControllerRef.current?.abort();
    setTurns([]);
    setQuery("");
    setActiveModule("chat");
  };

  const selectModule = (module: string) => {
    setActiveModule(module);
    if (module === "dataset-explorer" || module === "schema-explorer") {
      setIsDrawerOpen(true);
    }
  };

  const moduleTitle = MODULE_TITLES[activeModule];

  return (
    <div className="workspace-background flex h-screen min-h-[600px] flex-col overflow-hidden">
      <Header
        backendStatus={backendStatus}
        tableCount={schemas?.count}
        activeModule={activeModule}
        onSelectModule={selectModule}
        onOpenExplorer={() => setIsDrawerOpen(true)}
        onNewConversation={startNewConversation}
      />

      {activeModule === "chat" ? (
        <>
          <main className="flex min-h-0 flex-1 flex-col">
            {turns.length === 0 ? (
              <div className="flex min-h-0 flex-1 flex-col items-center justify-center overflow-y-auto px-4 py-8">
                <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-700 text-white shadow-lg shadow-violet-200">
                  <Sparkles className="h-7 w-7" />
                </div>
                <div className="max-w-2xl text-center">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-violet-700">
                    IndicSQL Studio
                  </p>
                  <h1 className="text-balance text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                    Ask your data, in your language.
                  </h1>
                  <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-500 sm:text-base">
                    Ask questions about NDAP datasets in English, Hindi, Hinglish,
                    Bengali, Tamil, Telugu, or Marathi.
                  </p>
                </div>

                <div className="mt-9 w-full max-w-3xl">
                  <div className="mb-3 flex items-center justify-center gap-2 text-xs font-medium text-slate-500">
                    <MessageSquareText className="h-4 w-4 text-violet-600" />
                    Try one of these questions
                  </div>
                  <SampleQuestions
                    onSelectQuestion={(sample) => setQuery(sample)}
                    disabled={backendStatus === "disconnected"}
                  />
                </div>
                {backendStatus === "disconnected" && (
                  <p className="mt-5 max-w-lg text-center text-xs text-amber-700">
                    Connect the IndicSQL backend to run a query. The API status is
                    shown in the header.
                  </p>
                )}
              </div>
            ) : (
              <div
                onScroll={(event) => {
                  const element = event.currentTarget;
                  setIsAtBottom(
                    element.scrollHeight - element.scrollTop - element.clientHeight < 120
                  );
                }}
                className="min-h-0 flex-1 overflow-y-auto px-4 py-7 sm:px-6"
                aria-live="polite"
                aria-label="Conversation"
              >
                <div className="mx-auto max-w-4xl space-y-8">
                  {turns.map((turn) => (
                    <article key={turn.id} className="space-y-5">
                      <div className="flex justify-end">
                        <div className="max-w-[88%] rounded-2xl rounded-br-md bg-violet-700 px-4 py-3 text-sm leading-6 text-white shadow-sm sm:max-w-[75%]">
                          {turn.question}
                        </div>
                      </div>
                      {turn.isLoading ? (
                        <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-5 text-sm text-slate-600 shadow-sm">
                          <LoaderCircle className="h-5 w-5 animate-spin text-violet-600" />
                          <span>Understanding your question and querying the database…</span>
                        </div>
                      ) : turn.error ? (
                        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm leading-6 text-rose-800">
                          <p className="font-semibold">Query could not be completed</p>
                          <p className="mt-1">{turn.error}</p>
                        </div>
                      ) : turn.response ? (
                        <div className="space-y-3">
                          <div className="flex items-center gap-2 px-1 text-xs font-semibold text-slate-500">
                            <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-violet-100 text-violet-700">
                              <Sparkles className="h-3.5 w-3.5" />
                            </span>
                            IndicSQL response
                          </div>
                          <ResultsWorkspace
                            data={turn.response}
                            isLoading={false}
                            error={null}
                          />
                        </div>
                      ) : null}
                    </article>
                  ))}
                  <div ref={bottomRef} />
                </div>
              </div>
            )}

            {!isAtBottom && turns.length > 0 && (
              <button
                type="button"
                onClick={() => bottomRef.current?.scrollIntoView({ behavior: "smooth" })}
                className="absolute bottom-28 left-1/2 z-10 -translate-x-1/2 rounded-full border border-slate-200 bg-white p-2 text-slate-600 shadow-lg hover:bg-slate-50"
                aria-label="Scroll to latest message"
              >
                <ArrowDown className="h-4 w-4" />
              </button>
            )}

            <div className="border-t border-slate-200/80 bg-white/90 px-4 py-4 backdrop-blur sm:px-6">
              <div className="mx-auto max-w-4xl">
                <QueryComposer
                  query={query}
                  onChange={setQuery}
                  onSubmit={handleQuerySubmit}
                  isLoading={turns.some((turn) => turn.isLoading)}
                  disabled={backendStatus === "disconnected"}
                  showSamples={false}
                />
                <p className="mt-2 flex items-center justify-center gap-1.5 text-[10px] text-slate-400">
                  <Database className="h-3 w-3" />
                  Read-only access to registered datasets · Language detected automatically
                </p>
              </div>
            </div>
          </main>
        </>
      ) : (
        <main className="flex-1 overflow-y-auto px-4 py-10 sm:px-8">
          <section className="mx-auto max-w-4xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-700">
              IndicSQL Workspace
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
              {moduleTitle}
            </h1>
            <div className="mt-7 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-violet-50 text-violet-700">
                {activeModule === "dataset-explorer" || activeModule === "schema-explorer" ? (
                  <Database className="h-5 w-5" />
                ) : (
                  <MessageSquareText className="h-5 w-5" />
                )}
              </div>
              <h2 className="mt-5 text-lg font-semibold text-slate-900">
                {activeModule === "dataset-explorer" || activeModule === "schema-explorer"
                  ? isLoadingSchemas
                    ? "Loading live schema catalog…"
                    : `${schemas?.count ?? 0} tables available from the backend`
                  : "This module is not connected yet"}
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                {schemasError &&
                (activeModule === "dataset-explorer" ||
                  activeModule === "schema-explorer")
                  ? schemasError
                  : MODULE_DESCRIPTIONS[activeModule] ||
                  "This module is not implemented in the current backend."}
              </p>
              {(activeModule === "dataset-explorer" ||
                activeModule === "schema-explorer") && (
                <Button
                  className="mt-5"
                  onClick={() => setIsDrawerOpen(true)}
                  disabled={!schemas}
                >
                  <Database className="h-4 w-4" />
                  Browse live schemas
                </Button>
              )}
              {activeModule === "research" && (
                <a
                  href="https://github.com/JHANKARBANSAL/INDIC_LANGUAGE"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-5 inline-flex text-sm font-semibold text-violet-700 hover:text-violet-900"
                >
                  Open project repository
                </a>
              )}
            </div>
            <button
              type="button"
              onClick={() => setActiveModule("chat")}
              className="mt-5 text-sm font-medium text-violet-700 hover:text-violet-900"
            >
              Return to AI Chat
            </button>
          </section>
        </main>
      )}

      <DatabaseDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        schemas={schemas}
        isLoading={isLoadingSchemas}
        error={schemasError}
      />
    </div>
  );
}
