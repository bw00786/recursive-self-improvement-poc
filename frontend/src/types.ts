export interface Champion {
  id: number;
  version: string;
  score: number;
  metrics: Record<string, number>;
  status: string;
  created_at: string;
  approved_by: string;
}

export interface Experiment {
  id: string;
  objective: string;
  parent_version: string;
  hypothesis: Record<string, unknown> | null;
  strategy: string | null;
  status: string;
  error: string | null;
  result_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface Candidate {
  id: string;
  experiment_id: string;
  parent_version: string;
  description: string;
  files_changed: string[];
  metrics: Record<string, number> | null;
  decision: {
    passed: boolean;
    hard_violations: string[];
    reasons: string[];
    candidate_score: number;
    champion_score: number;
    delta: number;
  } | null;
  status: string;
  created_at: string;
}

export interface Evaluation {
  id: number;
  candidate_id: string;
  metric_name: string;
  metric_value: number;
  baseline_value: number | null;
  delta: number | null;
  passed: boolean;
}

export interface Strategy {
  strategy: string;
  experiment_count: number;
  success_count: number;
  success_rate: number;
  average_improvement: number;
}

export interface DashboardMetrics {
  champion: { version: string; score: number; metrics: Record<string, number> } | null;
  experiments_total: number;
  experiments_promoted: number;
  experiments_rejected: number;
  experiments_failed: number;
  awaiting_approval: number;
  running: string[];
}

export interface Health {
  status: string;
  llm: string;
  ollama_reachable: boolean;
  mock_llm: boolean;
  docker_available: boolean;
  sandbox_mode: string;
  require_human_approval: boolean;
  langfuse_enabled: boolean;
}
