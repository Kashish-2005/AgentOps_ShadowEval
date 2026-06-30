import { useState } from "react";
import { motion } from "framer-motion";
import { apiClient, ApiError } from "../utils/api";
import type { PersonaInfo, RunResult } from "../types";

interface PersonaFormProps {
  personas: PersonaInfo[];
  loading: boolean;
  onResult: (result: RunResult) => void;
  onBatchResult: (results: RunResult[]) => void;
  onError: (message: string) => void;
  onLoadingChange: (loading: boolean) => void;
}

export function PersonaForm({
  personas,
  loading,
  onResult,
  onBatchResult,
  onError,
  onLoadingChange,
}: PersonaFormProps) {
  const [selected, setSelected] = useState<string>(
    personas[0]?.key ?? "skeptical_auditor"
  );
  const [concurrency, setConcurrency] = useState(3);

  async function handleSingle() {
    onLoadingChange(true);
    try {
      const result = await apiClient.evaluate(selected, concurrency);
      onResult(result);
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Evaluation failed");
    } finally {
      onLoadingChange(false);
    }
  }

  async function handleBatch() {
    onLoadingChange(true);
    try {
      const keys = personas.map((p) => p.key);
      const results = await apiClient.batchEvaluate(keys, concurrency);
      onBatchResult(results);
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Batch evaluation failed");
    } finally {
      onLoadingChange(false);
    }
  }

  return (
    <div className="card">
      <div className="card__header">
        <h2 className="card__title">Configure Evaluation</h2>
        <p className="card__subtitle">Select a persona to simulate</p>
      </div>

      <div className="persona-grid" role="radiogroup" aria-label="Select persona">
        {personas.map((p, i) => (
          <motion.label
            key={p.key}
            className={`persona-card ${selected === p.key ? "persona-card--selected" : ""}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07, duration: 0.3 }}
          >
            <input
              type="radio"
              name="persona"
              value={p.key}
              checked={selected === p.key}
              onChange={() => setSelected(p.key)}
              className="sr-only"
            />
            <span className="persona-card__name">{p.display_name}</span>
            <span className="persona-card__desc">{p.description}</span>
          </motion.label>
        ))}
      </div>

      <div className="concurrency-control">
        <div className="concurrency-control__header">
          <label htmlFor="concurrency" className="form-label">
            Concurrency Limit
          </label>
          <span className="concurrency-control__value mono">{concurrency}</span>
        </div>
        <input
          id="concurrency"
          type="range"
          min={1}
          max={10}
          value={concurrency}
          onChange={(e) => setConcurrency(Number(e.target.value))}
          className="range-slider"
          aria-label="Concurrency limit"
        />
        <div className="concurrency-control__ticks" aria-hidden="true">
          {Array.from({ length: 10 }, (_, i) => (
            <span key={i} className={i + 1 <= concurrency ? "tick tick--active" : "tick"} />
          ))}
        </div>
      </div>

      <div className="form-actions">
        <button
          className="btn-primary"
          onClick={handleSingle}
          disabled={loading || personas.length === 0}
          aria-busy={loading}
        >
          {loading ? (
            <>
              <span className="spinner" aria-hidden="true" />
              Evaluating...
            </>
          ) : (
            "Run Single"
          )}
        </button>
        <button
          className="btn-secondary"
          onClick={handleBatch}
          disabled={loading || personas.length === 0}
          aria-busy={loading}
        >
          {loading ? (
            <>
              <span className="spinner" aria-hidden="true" />
              Running...
            </>
          ) : (
            "Run All Personas"
          )}
        </button>
      </div>
    </div>
  );
}