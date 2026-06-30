import type {
  PersonaInfo,
  RunResult,
  EvaluationRecord,
  DashboardStats,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly endpoint: string,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

class ApiClient {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      const body = await response
        .json()
        .catch(() => ({ detail: "Request failed" }));
      throw new ApiError(
        response.status,
        endpoint,
        body.detail ?? body.message ?? "Request failed"
      );
    }
    return response.json() as Promise<T>;
  }

  async getPersonas(): Promise<PersonaInfo[]> {
    return this.request<PersonaInfo[]>("/api/v1/personas");
  }

  async evaluate(
    persona_name: string,
    concurrency_limit = 3
  ): Promise<RunResult> {
    return this.request<RunResult>("/api/v1/evaluate", {
      method: "POST",
      body: JSON.stringify({ persona_name, concurrency_limit }),
    });
  }

  async batchEvaluate(
    persona_names: string[],
    concurrency_limit = 3
  ): Promise<RunResult[]> {
    return this.request<RunResult[]>("/api/v1/evaluate/batch", {
      method: "POST",
      body: JSON.stringify({ persona_names, concurrency_limit }),
    });
  }

  async getHistory(
    persona?: string,
    limit = 50
  ): Promise<EvaluationRecord[]> {
    const params = new URLSearchParams();
    if (persona) params.set("persona", persona);
    params.set("limit", String(limit));
    return this.request<EvaluationRecord[]>(`/api/v1/history?${params}`);
  }

  async getStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>("/api/v1/stats");
  }

  async deleteEvaluation(id: number): Promise<{ deleted: boolean }> {
    return this.request<{ deleted: boolean }>(`/api/v1/history/${id}`, {
      method: "DELETE",
    });
  }

  async checkHealth(): Promise<boolean> {
    try {
      await this.request("/health");
      return true;
    } catch {
      return false;
    }
  }
}

export const apiClient = new ApiClient();