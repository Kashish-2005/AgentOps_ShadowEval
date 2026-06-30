export type PersonaKey =
  | "skeptical_auditor"
  | "frustrated_consumer"
  | "power_user"
  | "naive_first_timer"
  | "adversarial_tester";

export interface PersonaInfo {
  key: string;
  display_name: string;
  description: string;
}

export interface EvaluationReport {
  task_completed: boolean;
  efficiency_score: number;
  loop_detected: boolean;
  hallucination_risk: "low" | "medium" | "high";
  total_tool_calls: number;
  success_rate: number;
  persona_name: string;
  latency_ms: number;
  notes: string[];
  risk_factors: string[];
}

export interface RunResult {
  run_id: string;
  persona_name: string;
  persona_display_name: string;
  latency_ms: number;
  simulated_token_count: number;
  loop_detected: boolean;
  evaluation: EvaluationReport;
  tool_sequence: string[];
  _timestamp?: string;
  _persisted?: boolean;
}

export interface EvaluationRecord {
  id: number;
  persona: string;
  persona_display_name: string;
  latency_ms: number;
  tokens: number;
  efficiency_score: number;
  loop_detected: boolean;
  hallucination_risk: string;
  task_completed: boolean;
  success_rate: number;
  tool_sequence: string[];
  notes: string[];
  risk_factors: string[];
  timestamp: string;
}

export interface DashboardStats {
  total_runs: number;
  avg_efficiency: number;
  avg_latency_ms: number;
  loop_detection_rate: number;
  risk_distribution: Record<string, number>;
  runs_by_persona: Record<string, number>;
}

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
  duration: number;
}