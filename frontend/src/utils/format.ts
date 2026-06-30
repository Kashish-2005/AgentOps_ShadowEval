export function formatLatency(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function formatScore(score: number): string {
  return `${score} / 10`;
}

export function formatSuccessRate(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}

export function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-IN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function formatToolSequence(tools: string[]): string {
  return tools.join(" → ");
}

export function getRiskColor(risk: string): string {
  if (risk === "high") return "var(--risk-high)";
  if (risk === "medium") return "var(--risk-medium)";
  return "var(--risk-low)";
}

export function getRiskBg(risk: string): string {
  if (risk === "high") return "rgba(255,71,87,0.15)";
  if (risk === "medium") return "rgba(255,184,0,0.15)";
  return "rgba(46,213,115,0.15)";
}

export function getScoreColor(score: number): string {
  if (score <= 3) return "var(--accent-red)";
  if (score <= 6) return "var(--accent-amber)";
  return "var(--accent-green)";
}

export function getScoreWidth(score: number): string {
  return `${(score / 10) * 100}%`;
}