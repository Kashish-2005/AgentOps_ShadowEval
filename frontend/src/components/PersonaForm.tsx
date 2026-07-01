import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
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

type Mode = "simulate" | "custom";

export function PersonaForm({
  personas,
  loading,
  onResult,
  onBatchResult,
  onError,
  onLoadingChange,
}: PersonaFormProps) {
  const [mode, setMode] = useState<Mode>("simulate");
  const [selected, setSelected] = useState<string>(
    personas[0]?.key ?? "skeptical_auditor"
  );
  const [concurrency, setConcurrency] = useState(3);
  const [customPrompt, setCustomPrompt] = useState("");
  const [customPersona, setCustomPersona] = useState("power_user");

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

  async function handleCustomEval() {
    if (!customPrompt.trim()) {
      onError("Please enter a prompt before evaluating.");
      return;
    }
    onLoadingChange(true);
    try {
      const result = await apiClient.evaluateCustom(customPrompt.trim(), customPersona);
      onResult(result);
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Custom evaluation failed");
    } finally {
      onLoadingChange(false);
    }
  }

  return (
    <div className="card">
      <div className="card__header">
        <h2 className="card__title">Configure Evaluation</h2>
        <p className="card__subtitle">
          Simulate a persona or test your own prompt
        </p>
      </div>

      {/* Mode Toggle */}
      <div className="mode-toggle" role="tablist" aria-label="Evaluation mode">
        <button
          role="tab"
          aria-selected={mode === "simulate"}
          className={`mode-tab ${mode === "simulate" ? "mode-tab--active" : ""}`}
          onClick={() => setMode("simulate")}
        >
          Simulate Persona
        </button>
        <button
          role="tab"
          aria-selected={mode === "custom"}
          className={`mode-tab ${mode === "custom" ? "mode-tab--active" : ""}`}
          onClick={() => setMode("custom")}
        >
          Test My Prompt
        </button>
      </div>

      <AnimatePresence mode="wait">

        {/* ── Simulate Mode ── */}
        {mode === "simulate" && (
          <motion.div
            key="simulate"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
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
                  <span
                    key={i}
                    className={i + 1 <= concurrency ? "tick tick--active" : "tick"}
                  />
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
                  <><span className="spinner" aria-hidden="true" />Evaluating...</>
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
                  <><span className="spinner" aria-hidden="true" />Running...</>
                ) : (
                  "Run All Personas"
                )}
              </button>
            </div>
          </motion.div>
        )}

        {/* ── Custom Prompt Mode ── */}
        {mode === "custom" && (
          <motion.div
            key="custom"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="custom-eval-panel"
          >
            <div className="custom-eval-intro">
              <p className="custom-eval-desc">
                Enter any text and our framework evaluates it through a real
                LLM call via HuggingFace. Results include hallucination risk,
                efficiency scoring, and loop detection — applied to your actual input.
              </p>
            </div>

            <div className="custom-field">
              <label htmlFor="custom-prompt" className="form-label">
                Your Prompt
              </label>
              <textarea
                id="custom-prompt"
                className="custom-textarea"
                placeholder="e.g. Summarize the key risks of deploying LLM agents in production environments without proper evaluation frameworks..."
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                rows={5}
                maxLength={2000}
                aria-label="Custom prompt for evaluation"
                disabled={loading}
              />
              <div className="custom-textarea-footer">
                <span className={`char-count mono ${customPrompt.length > 1800 ? "char-count--warn" : ""}`}>
                  {customPrompt.length} / 2000
                </span>
              </div>
            </div>

            <div className="custom-field">
              <label htmlFor="custom-persona" className="form-label">
                Evaluate As Persona
              </label>
              <select
                id="custom-persona"
                className="custom-select"
                value={customPersona}
                onChange={(e) => setCustomPersona(e.target.value)}
                disabled={loading}
                aria-label="Select persona for custom evaluation"
              >
                {personas.map((p) => (
                  <option key={p.key} value={p.key}>
                    {p.display_name}
                  </option>
                ))}
              </select>
              <p className="custom-field-hint">
                Persona affects scoring weights and risk tolerance applied to your prompt's evaluation.
              </p>
            </div>

            <div className="form-actions">
              <button
                className="btn-primary"
                onClick={handleCustomEval}
                disabled={loading || customPrompt.trim().length === 0}
                aria-busy={loading}
              >
                {loading ? (
                  <><span className="spinner" aria-hidden="true" />Evaluating via LLM...</>
                ) : (
                  "Evaluate My Prompt"
                )}
              </button>
            </div>

            {customPrompt.trim().length === 0 && (
              <p className="custom-empty-hint">
                Enter a prompt above to enable evaluation.
              </p>
            )}
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}