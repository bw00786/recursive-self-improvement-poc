const BASE = import.meta.env.VITE_API_URL || "";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

export const api = {
  health: () => req<import("../types").Health>("/api/health"),
  metrics: () => req<import("../types").DashboardMetrics>("/api/metrics"),
  champion: () => req<import("../types").Champion>("/api/champion"),
  champions: () => req<import("../types").Champion[]>("/api/champions"),
  experiments: () => req<import("../types").Experiment[]>("/api/experiments"),
  experiment: (id: string) => req<import("../types").Experiment>(`/api/experiments/${id}`),
  experimentCandidates: (id: string) =>
    req<import("../types").Candidate[]>(`/api/experiments/${id}/candidates`),
  createExperiment: () =>
    req<import("../types").Experiment>("/api/experiments", {
      method: "POST",
      body: JSON.stringify({ objective: "Improve the benchmark score" }),
    }),
  runExperiment: (id: string) =>
    req<import("../types").Experiment>(`/api/experiments/${id}/run`, { method: "POST" }),
  candidates: () => req<import("../types").Candidate[]>("/api/candidates"),
  candidate: (id: string) => req<import("../types").Candidate>(`/api/candidates/${id}`),
  evaluations: (candidateId: string) =>
    req<import("../types").Evaluation[]>(`/api/evaluations/${candidateId}`),
  approve: (id: string) =>
    req(`/api/candidates/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved_by: "human", reason: "approved via UI" }),
    }),
  reject: (id: string) =>
    req(`/api/candidates/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ approved_by: "human", reason: "rejected via UI" }),
    }),
  strategies: () => req<import("../types").Strategy[]>("/api/strategies"),
  runBaseline: () =>
    req<import("../types").Champion>("/api/benchmark/run", { method: "POST" }),
};
