import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { RunResult, EvaluationRecord } from "../types";
import {
  formatLatency,
  formatTimestamp,
  getRiskColor,
  getRiskBg,
  getScoreColor,
  getScoreWidth,
} from "../utils/format";

type Row = RunResult | EvaluationRecord;
type SortKey = "persona" | "latency" | "tokens" | "score" | "risk";
type SortDir = "asc" | "desc";

function isRecord(r: Row): r is EvaluationRecord {
  return "id" in r && typeof (r as EvaluationRecord).id === "number";
}

function getPersonaName(r: Row): string {
  return isRecord(r) ? r.persona_display_name : r.persona_display_name;
}
function getLatency(r: Row): number {
  return r.latency_ms;
}
function getTokens(r: Row): number {
  return isRecord(r) ? r.tokens : r.simulated_token_count;
}
function getScore(r: Row): number {
  return isRecord(r) ? r.efficiency_score : r.evaluation.efficiency_score;
}
function getRisk(r: Row): string {
  return isRecord(r) ? r.hallucination_risk : r.evaluation.hallucination_risk;
}
function getLoop(r: Row): boolean {
  return isRecord(r) ? r.loop_detected : r.loop_detected;
}
function getTimestamp(r: Row): string {
  return isRecord(r) ? r.timestamp : r._timestamp ?? "";
}
function getTools(r: Row): string[] {
  return r.tool_sequence;
}

interface ResultsTableProps {
  results: Row[];
  onDelete?: (id: number) => void;
}

export function ResultsTable({ results, onDelete }: ResultsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("latency");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

  const displayed = results.slice(0, 50);

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  const sorted = [...displayed].sort((a, b) => {
    let av = 0;
    let bv = 0;
    if (sortKey === "latency") { av = getLatency(a); bv = getLatency(b); }
    if (sortKey === "tokens") { av = getTokens(a); bv = getTokens(b); }
    if (sortKey === "score") { av = getScore(a); bv = getScore(b); }
    if (sortKey === "risk") {
      const m: Record<string, number> = { low: 0, medium: 1, high: 2 };
      av = m[getRisk(a)] ?? 0;
      bv = m[getRisk(b)] ?? 0;
    }
    if (sortKey === "persona") {
      return sortDir === "asc"
        ? getPersonaName(a).localeCompare(getPersonaName(b))
        : getPersonaName(b).localeCompare(getPersonaName(a));
    }
    return sortDir === "asc" ? av - bv : bv - av;
  });

  const SortBtn = ({ col, label }: { col: SortKey; label: string }) => (
    <button
      className="th-btn"
      onClick={() => handleSort(col)}
      aria-sort={sortKey === col ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
    >
      {label}
      <span className="th-arrow" aria-hidden="true">
        {sortKey === col ? (sortDir === "asc" ? " ↑" : " ↓") : " ↕"}
      </span>
    </button>
  );

  if (results.length === 0) {
    return (
      <div className="card">
        <h2 className="card__title">Evaluation History</h2>
        <div className="empty-state">
          <div className="empty-state__icon" aria-hidden="true">◎</div>
          <p className="empty-state__title">No evaluations yet</p>
          <p className="empty-state__sub">Run a persona above to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card__header">
        <h2 className="card__title">
          Evaluation History
          <span className="count-badge mono">{results.length}</span>
        </h2>
        {results.length > 50 && (
          <p className="table-note">Showing 50 most recent</p>
        )}
      </div>
      <div className="table-wrap">
        <table className="results-table" aria-label="Evaluation results">
          <thead>
            <tr>
              <th><SortBtn col="persona" label="Persona" /></th>
              <th><SortBtn col="latency" label="Latency" /></th>
              <th><SortBtn col="tokens" label="Tokens" /></th>
              <th><SortBtn col="score" label="Score" /></th>
              <th><SortBtn col="risk" label="Risk" /></th>
              <th>Loop</th>
              <th>Tools</th>
              <th>Time</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <AnimatePresence initial={false}>
              {sorted.map((row, i) => {
                const isNewest = i === 0 && !isRecord(row);
                const risk = getRisk(row);
                const score = getScore(row);
                const loop = getLoop(row);
                const tools = getTools(row);
                const ts = getTimestamp(row);
                const rowId = isRecord(row) ? row.id : null;

                return (
                  <motion.tr
                    key={isRecord(row) ? `rec-${row.id}` : `run-${(row as RunResult).run_id}`}
                    className={`results-row ${isNewest ? "results-row--newest" : ""}`}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2, delay: i * 0.03 }}
                  >
                    <td>
                      <div className="cell-persona">
                        <span className="cell-persona__name">{getPersonaName(row)}</span>
                        {isRecord(row) && (
                          <span className="db-badge mono">DB</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="mono cell-latency">{formatLatency(getLatency(row))}</span>
                    </td>
                    <td>
                      <span className="mono">{getTokens(row).toLocaleString()}</span>
                    </td>
                    <td>
                      <div className="score-bar-wrap">
                        <div className="score-bar-track">
                          <div
                            className="score-bar-fill"
                            style={{
                              width: getScoreWidth(score),
                              backgroundColor: getScoreColor(score),
                            }}
                          />
                        </div>
                        <span
                          className="score-text mono"
                          style={{ color: getScoreColor(score) }}
                        >
                          {score}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span
                        className="risk-badge"
                        style={{
                          color: getRiskColor(risk),
                          backgroundColor: getRiskBg(risk),
                        }}
                      >
                        {risk}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`loop-dot ${loop ? "loop-dot--active" : "loop-dot--clean"}`}
                        aria-label={loop ? "Loop detected" : "No loop"}
                        title={loop ? "Loop detected" : "No loop"}
                      />
                    </td>
                    <td>
                      <div className="tools-cell">
                        {tools.slice(0, 2).map((t, ti) => (
                          <span key={ti} className="tool-chip mono">{t.replace("_", " ")}</span>
                        ))}
                        {tools.length > 2 && (
                          <span className="tool-chip tool-chip--more mono">+{tools.length - 2}</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="mono cell-time">
                        {ts ? formatTimestamp(ts) : "—"}
                      </span>
                    </td>
                    <td>
                      {rowId !== null && onDelete && (
                        confirmDelete === rowId ? (
                          <div className="delete-confirm">
                            <button
                              className="delete-yes"
                              onClick={() => {
                                onDelete(rowId);
                                setConfirmDelete(null);
                              }}
                            >Yes</button>
                            <button
                              className="delete-no"
                              onClick={() => setConfirmDelete(null)}
                            >No</button>
                          </div>
                        ) : (
                          <button
                            className="delete-btn"
                            onClick={() => setConfirmDelete(rowId)}
                            aria-label="Delete record"
                          >
                            ✕
                          </button>
                        )
                      )}
                    </td>
                  </motion.tr>
                );
              })}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
    </div>
  );
}