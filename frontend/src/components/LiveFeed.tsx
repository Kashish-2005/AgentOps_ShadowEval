import { motion, AnimatePresence } from "framer-motion";
import type { RunResult } from "../types";
import { formatLatency, getRiskColor, getRiskBg } from "../utils/format";

interface LiveFeedProps {
  results: RunResult[];
}

export function LiveFeed({ results }: LiveFeedProps) {
  const recent = results.slice(0, 5);

  return (
    <div className="card live-feed">
      <h2 className="card__title">Live Feed</h2>
      {recent.length === 0 ? (
        <p className="empty-hint">Waiting for evaluations…</p>
      ) : (
        <AnimatePresence initial={false}>
          {recent.map((r) => {
            const risk = r.evaluation.hallucination_risk;
            return (
              <motion.div
                key={r.run_id}
                className="live-row"
                style={{ borderLeftColor: getRiskColor(risk) }}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.25 }}
              >
                <div className="live-row__top">
                  <span className="live-row__name">{r.persona_display_name}</span>
                  <span className="live-row__latency mono">{formatLatency(r.latency_ms)}</span>
                </div>
                <div className="live-row__bottom">
                  <span
                    className="risk-badge risk-badge--sm"
                    style={{ color: getRiskColor(risk), backgroundColor: getRiskBg(risk) }}
                  >
                    {risk}
                  </span>
                  <span className="live-row__score mono">
                    {r.evaluation.efficiency_score}/10
                  </span>
                  {r.loop_detected && (
                    <span className="live-row__loop">⚠ loop</span>
                  )}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      )}
    </div>
  );
}