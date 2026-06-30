import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, ReferenceLine,
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
} from "recharts";
import type { RunResult, EvaluationRecord } from "../types";
import { formatLatency } from "../utils/format";

type Row = RunResult | EvaluationRecord;

function isRecord(r: Row): r is EvaluationRecord {
  return "id" in r && typeof (r as EvaluationRecord).id === "number";
}

interface ChartPoint {
  persona: string;
  latency: number;
  efficiency: number;
  tokens: number;
}

interface TimePoint {
  index: number;
  latency: number;
  persona: string;
}

const tooltipStyle = {
  backgroundColor: "var(--bg-tertiary)",
  border: "1px solid var(--border)",
  borderRadius: "8px",
  fontFamily: "'JetBrains Mono', monospace",
  fontSize: "12px",
  color: "var(--text-primary)",
};

interface MetricsChartProps {
  results: Row[];
}

export function MetricsChart({ results }: MetricsChartProps) {
  const byPersona = useMemo<ChartPoint[]>(() => {
    const map: Record<string, { lat: number[]; eff: number[]; tok: number[] }> = {};
    for (const r of results) {
      const name = isRecord(r) ? r.persona_display_name : r.persona_display_name;
      const lat = r.latency_ms;
      const eff = isRecord(r) ? r.efficiency_score : r.evaluation.efficiency_score;
      const tok = isRecord(r) ? r.tokens : r.simulated_token_count;
      if (!map[name]) map[name] = { lat: [], eff: [], tok: [] };
      map[name].lat.push(lat);
      map[name].eff.push(eff);
      map[name].tok.push(tok);
    }
    return Object.entries(map).map(([persona, v]) => ({
      persona: persona.length > 14 ? persona.slice(0, 12) + "…" : persona,
      latency: Math.round(v.lat.reduce((a, b) => a + b, 0) / v.lat.length),
      efficiency: parseFloat((v.eff.reduce((a, b) => a + b, 0) / v.eff.length).toFixed(1)),
      tokens: Math.round(v.tok.reduce((a, b) => a + b, 0) / v.tok.length),
    }));
  }, [results]);

  const timeSeries = useMemo<TimePoint[]>(() => {
    return results
      .slice()
      .reverse()
      .map((r, i) => ({
        index: i + 1,
        latency: Math.round(r.latency_ms),
        persona: isRecord(r) ? r.persona_display_name : r.persona_display_name,
      }));
  }, [results]);

  const avgLatency = useMemo(() => {
    if (!timeSeries.length) return 0;
    return Math.round(
      timeSeries.reduce((a, b) => a + b.latency, 0) / timeSeries.length
    );
  }, [timeSeries]);

  const radarData = useMemo(() => {
    return byPersona.map((p) => ({
      persona: p.persona,
      Efficiency: p.efficiency,
      "Avg Latency": Math.min(10, Math.round(p.latency / 100)),
      Tokens: Math.min(10, Math.round(p.tokens / 100)),
    }));
  }, [byPersona]);

  if (results.length === 0) {
    return (
      <div className="card">
        <h2 className="card__title">Performance Metrics</h2>
        <div className="empty-state">
          <div className="empty-state__icon" aria-hidden="true">◈</div>
          <p className="empty-state__title">No data yet</p>
          <p className="empty-state__sub">Charts will appear after the first evaluation</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      className="card"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3, duration: 0.5 }}
    >
      <h2 className="card__title">Performance Metrics</h2>

      <div className="charts-grid">
        <div className="chart-box">
          <p className="chart-label">Avg Latency by Persona</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={byPersona} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="persona" tick={{ fill: "var(--text-muted)", fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: "var(--text-muted)", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(v) => formatLatency(v)} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => [formatLatency(Number(v)), "Latency"]} cursor={{ fill: "rgba(0,212,255,0.05)" }} />
              <Bar dataKey="latency" fill="var(--accent-cyan)" radius={[4, 4, 0, 0]} isAnimationActive animationDuration={800} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-box">
          <p className="chart-label">Avg Efficiency Score</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={byPersona} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="persona" tick={{ fill: "var(--text-muted)", fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 10]} tick={{ fill: "var(--text-muted)", fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v} / 10`, "Efficiency"]} cursor={{ fill: "rgba(0,180,160,0.05)" }} />
              <Bar dataKey="efficiency" fill="var(--accent-teal)" radius={[4, 4, 0, 0]} isAnimationActive animationDuration={800} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {timeSeries.length > 1 && (
        <div className="chart-box chart-box--full">
          <p className="chart-label">Latency Over Time</p>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={timeSeries} margin={{ top: 8, right: 16, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="index" tick={{ fill: "var(--text-muted)", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(v) => `#${v}`} />
              <YAxis tick={{ fill: "var(--text-muted)", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(v) => formatLatency(v)} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v, _, p) => [formatLatency(Number(v)), p.payload.persona]} />
              <ReferenceLine y={avgLatency} stroke="var(--accent-amber)" strokeDasharray="4 2" label={{ value: "avg", fill: "var(--accent-amber)", fontSize: 11, fontFamily: "JetBrains Mono" }} />
              <Line type="monotone" dataKey="latency" stroke="var(--accent-cyan)" strokeWidth={2} dot={{ fill: "var(--accent-cyan)", r: 3, strokeWidth: 0 }} activeDot={{ r: 5, fill: "var(--accent-cyan)" }} isAnimationActive animationDuration={800} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {radarData.length >= 2 && (
        <div className="chart-box chart-box--full">
          <p className="chart-label">Persona Fingerprint</p>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData} margin={{ top: 8, right: 40, left: 40, bottom: 8 }}>
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis dataKey="persona" tick={{ fill: "var(--text-secondary)", fontSize: 11 }} />
              <Radar name="Efficiency" dataKey="Efficiency" stroke="var(--accent-cyan)" fill="var(--accent-cyan)" fillOpacity={0.15} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}
    </motion.div>
  );
}