"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  BarChart3,
  BookOpen,
  ChevronRight,
  Database,
  FileSearch,
  FlaskConical,
  Github,
  History,
  Info,
  Languages,
  Menu,
  MessageSquareText,
  Moon,
  ShieldCheck,
  Sun,
  Workflow,
  X,
} from "lucide-react";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { Button } from "@/components/ui/Button";

interface HeaderProps {
  backendStatus: "connected" | "disconnected" | "checking";
  tableCount?: number;
  activeModule: string;
  onSelectModule: (module: string) => void;
  onOpenExplorer: () => void;
  onNewConversation: () => void;
}

const NAVIGATION = [
  {
    title: "Main",
    items: [
      { id: "overview", label: "Overview", icon: BarChart3 },
      { id: "chat", label: "AI Chat / SQL Playground", icon: MessageSquareText },
      { id: "query-history", label: "Query History", icon: History },
    ],
  },
  {
    title: "SQL Intelligence",
    items: [
      { id: "sql-quality", label: "SQL Quality Inspector", icon: ShieldCheck },
      { id: "ai-reviewer", label: "AI SQL Reviewer", icon: FileSearch },
      { id: "sql-inspector", label: "SQL Inspector", icon: Activity },
      { id: "pipeline-explorer", label: "Query Pipeline Explorer", icon: Workflow },
    ],
  },
  {
    title: "Analytics & Evaluation",
    items: [
      { id: "benchmark-dashboard", label: "Benchmark Dashboard", icon: BarChart3 },
      { id: "benchmark-explorer", label: "Benchmark Explorer", icon: FlaskConical },
      { id: "language-analytics", label: "Language Analytics", icon: Languages },
      { id: "model-comparison", label: "Model Comparison", icon: Activity },
      { id: "failure-analysis", label: "Failure Analysis", icon: FileSearch },
    ],
  },
  {
    title: "Database",
    items: [
      { id: "dataset-explorer", label: "Dataset Explorer", icon: Database },
      { id: "schema-explorer", label: "Schema Explorer", icon: FileSearch },
    ],
  },
  {
    title: "Resources",
    items: [
      { id: "research", label: "Research & Documentation", icon: BookOpen },
      { id: "about", label: "About IndicSQL", icon: Info },
    ],
  },
];

const MODULE_TITLES = NAVIGATION.flatMap((section) => section.items).reduce<
  Record<string, string>
>((titles, item) => {
  titles[item.id] = item.label;
  return titles;
}, {});

export function Header({
  backendStatus,
  tableCount,
  activeModule,
  onSelectModule,
  onOpenExplorer,
  onNewConversation,
}: HeaderProps) {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const currentTitle = MODULE_TITLES[activeModule] || "AI Chat / SQL Playground";

  useEffect(() => {
    const savedTheme = window.localStorage.getItem("indicsql-theme");
    const dark =
      savedTheme === "dark" ||
      (savedTheme === null &&
        window.matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.classList.toggle("dark", dark);
    setIsDark(dark);
  }, []);

  const toggleTheme = () => {
    const nextIsDark = !isDark;
    document.documentElement.classList.toggle("dark", nextIsDark);
    window.localStorage.setItem("indicsql-theme", nextIsDark ? "dark" : "light");
    setIsDark(nextIsDark);
  };

  const selectModule = (module: string) => {
    onSelectModule(module);
    setNavigationOpen(false);
    if (module === "dataset-explorer" || module === "schema-explorer") {
      onOpenExplorer();
    }
  };

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-[68px] max-w-[1440px] items-center justify-between px-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              onClick={() => setNavigationOpen(true)}
              className="rounded-xl p-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
              aria-label="Open navigation menu"
              aria-expanded={navigationOpen}
            >
              <Menu className="h-5 w-5" />
            </button>
            <button
              type="button"
              onClick={onNewConversation}
              className="flex min-w-0 items-center gap-2.5 text-left"
              aria-label="Start a new IndicSQL conversation"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-indigo-700 text-sm font-bold text-white shadow-sm">
                I
              </span>
              <span className="min-w-0">
                <span className="block truncate text-[15px] font-bold tracking-tight text-slate-950">
                  IndicSQL Studio
                </span>
                <span className="hidden text-[11px] text-slate-500 sm:block">
                  Multilingual Database Intelligence
                </span>
              </span>
            </button>
            <ChevronRight className="hidden h-4 w-4 text-slate-300 md:block" />
            <span className="hidden truncate text-sm font-medium text-slate-600 md:block">
              {currentTitle}
            </span>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <button
              type="button"
              onClick={toggleTheme}
              className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
              aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
              aria-pressed={isDark}
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <div className="hidden sm:block">
              <StatusIndicator status={backendStatus} tableCount={tableCount} />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenExplorer}
              className="hidden border-slate-200 text-slate-700 sm:inline-flex"
            >
              <Database className="h-4 w-4 text-violet-700" />
              <span className="hidden md:inline">Datasets</span>
            </Button>
            <a
              href="https://github.com/JHANKARBANSAL/INDIC_LANGUAGE"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="IndicSQL GitHub repository"
              className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
            >
              <Github className="h-4 w-4" />
            </a>
          </div>
        </div>
        <div className="border-t border-slate-100 px-4 py-2 sm:hidden">
          <StatusIndicator status={backendStatus} tableCount={tableCount} />
        </div>
      </header>

      {navigationOpen && (
        <div className="fixed inset-0 z-50">
          <button
            type="button"
            aria-label="Close navigation menu"
            className="absolute inset-0 bg-slate-950/35 backdrop-blur-[2px]"
            onClick={() => setNavigationOpen(false)}
          />
          <aside
            className="nav-drawer-enter relative flex h-full w-[min(88vw,340px)] flex-col overflow-y-auto border-r border-slate-200 bg-white shadow-2xl"
            aria-label="Application navigation"
          >
            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-5">
              <div>
                <p className="text-sm font-bold text-slate-950">IndicSQL Studio</p>
                <p className="mt-0.5 text-xs text-slate-500">Workspace navigation</p>
              </div>
              <button
                type="button"
                onClick={() => setNavigationOpen(false)}
                className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
                aria-label="Close navigation"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <nav className="flex-1 space-y-5 px-3 py-5">
              {NAVIGATION.map((section) => (
                <section key={section.title}>
                  <h2 className="px-3 pb-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
                    {section.title}
                  </h2>
                  <div className="space-y-1">
                    {section.items.map(({ id, label, icon: Icon }) => {
                      const selected = id === activeModule;
                      return (
                        <button
                          key={id}
                          type="button"
                          onClick={() => selectModule(id)}
                          className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[13px] transition ${
                            selected
                              ? "bg-violet-50 font-semibold text-violet-800"
                              : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                          }`}
                          aria-current={selected ? "page" : undefined}
                        >
                          <Icon className="h-4 w-4 shrink-0" />
                          <span className="flex-1">{label}</span>
                          {selected && <span className="h-1.5 w-1.5 rounded-full bg-violet-600" />}
                        </button>
                      );
                    })}
                  </div>
                </section>
              ))}
            </nav>
            <div className="border-t border-slate-100 px-5 py-4 text-[11px] leading-5 text-slate-400">
              IndicSQL · Uses live backend services where available
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
