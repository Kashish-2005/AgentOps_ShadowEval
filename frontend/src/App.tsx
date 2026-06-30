import { useState, useEffect, useCallback } from "react";
import { Header } from "./components/Header";
import { StatCard } from "./components/StatCard";
import { PersonaForm } from "./components/PersonaForm";
import { LiveFeed } from "./components/LiveFeed";
import { MetricsChart } from "./components/MetricsChart";
import { ResultsTable } from "./components/ResultsTable";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { ToastContainer } from "./components/Toast";
import { useToast } from "./hooks/useToast";
import { apiClient } from "./utils/api";
import { formatLatency } from "./utils/format";
import type {
  RunResult,
  EvaluationRecord,
  PersonaInfo,
  DashboardStats,
} from "./types";

export default function App() {
  const [results, setResults] = useState<RunResult[]>([]);
  const [history, setHistory] = useState<EvaluationRecord[]>([]);
  const [personas, setPersonas] = useState<PersonaInfo[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [backendOnline, setBackendOnline] = useState(false);
  const { toasts, showToast, dismissToast } = useToast();

  const refreshStats = useCallback(async () => {
    try {
      const s = await apiClient.getStats();
      setStats(s);
    } catch {
      // non-critical
    }
  }, []);

  useEffect(() => {
    async function init() {
      const online = await apiClient.checkHealth();
      setBackendOnline(online);

      const settled = await Promise.allSettled([
        apiClient.getPersonas(),
        apiClient.getHistory(),
        apiClient.getStats(),
      ]);

      if (settled[0].status === "fulfilled") setPersonas(settled[0].value);
      else showToast("Could not load personas", "error");

      if (settled[1].status === "fulfilled") setHistory(settled[1].value);
      else showToast("Could not load history", "warning");

      if (settled[2].status === "fulfilled") setStats(settled[2].value);

      setInitializing(false);
    }
    init();
  }, []);

  const handleResult = useCallback(
    (result: RunResult) => {
      const stamped: RunResult = {
        ...result,
        _timestamp: new Date().toISOString(),
        _persisted: true,
      };
      setResults((prev) => [stamped, ...prev]);
      showToast(`${result.persona_display_name} — score ${result.evaluation.efficiency_score}/10`, "success");
      refreshStats();
    },
    [showToast, refreshStats]
  );

  const handleBatchResult = useCallback(
    (batchResults: RunResult[]) => {
      const stamped = batchResults.map((r) => ({
        ...r,
        _timestamp: new Date().toISOString(),
        _persisted: true,
      }));
      setResults((prev) => [...stamped, ...prev]);
      showToast(`Batch complete — ${batchResults.length} evaluations`, "success");
      refreshStats();
    },
    [showToast, refreshStats]
  );

  const handleDelete = useCallback(
    async (id: number) => {
      try {
        const { deleted } = await apiClient.deleteEvaluation(id);
        if (deleted) {
          setHistory((prev) => prev.filter((r) => r.id !== id));
          showToast("Record deleted", "warning");
          refreshStats();
        }
      } catch {
        showToast("Delete failed", "error");
      }
    },
    [showToast, refreshStats]
  );

  const statCards = [
    {
      label: "Total Runs",
      value: stats?.total_runs ?? results.length + history.length,
      icon: "⚡",
      index: 0,
    },
    {
      label: "Avg Efficiency",
      value: stats ? stats.avg_efficiency.toFixed(1) : "—",
      unit: "/ 10",
      icon: "📊",
      index: 1,
    },
    {
      label: "Avg Latency",
      value: stats ? formatLatency(stats.avg_latency_ms) : "—",
      icon: "⏱",
      index: 2,
    },
    {
      label: "Loop Rate",
      value: stats ? `${(stats.loop_detection_rate * 100).toFixed(0)}%` : "—",
      icon: "🔄",
      highlight: stats ? stats.loop_detection_rate > 0.3 : false,
      index: 3,
    },
  ];

  const allRows = [...results, ...history];

  return (
    <div className="app-shell">
      <Header
        runCount={results.length + history.length}
        backendOnline={backendOnline}
      />

      <main className="main-content" id="main">
        <div className="stats-grid">
          {statCards.map((c) => (
            <StatCard key={c.label} {...c} loading={initializing} />
          ))}
        </div>

        <div className="form-row">
          <div className="form-col">
            <PersonaForm
              personas={personas}
              loading={loading}
              onResult={handleResult}
              onBatchResult={handleBatchResult}
              onError={(msg) => showToast(msg, "error")}
              onLoadingChange={setLoading}
            />
          </div>
          <div className="live-col">
            <LiveFeed results={results} />
          </div>
        </div>

        <ErrorBoundary>
          <MetricsChart results={allRows} />
        </ErrorBoundary>

        <ErrorBoundary>
          <ResultsTable results={allRows} onDelete={handleDelete} />
        </ErrorBoundary>
      </main>

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}