export type Article = { id: string; title: string; excerpt: string; publisher: string; url: string; published_at: string; provenance?: string };
export type Evidence = { id: string; article: Article; stance: string; reasoning: string; at: string };
export type Revision = { id: string; probability: number; rationale: string; at: string; provider: string; model: string };
export type Forecast = {
  id: string;
  map_id: string;
  parent_id: string | null;
  original: {
    title: string; domain: string; scenario: string; probability: number; reasoning: string;
    assumptions: string[]; alternatives: string[]; weaknesses: string[]; confirm_if: string; refute_if: string;
    provenance: { provider: string; model: string };
  };
  probability: number;
  joint_probability: number | null;
  issued_at: string;
  deadline: string;
  status: string;
  truth_value: number | null;
  evidence: Evidence[];
  revisions: Revision[];
  resolution: { reasoning: string; credibility: string; article: Article | null } | null;
};
export type MapDetails = {
  id: string;
  event: { title: string; date: string; classification: string; actors: string[]; regions: string[]; reported_developments: string[]; unverified_claims: string[] };
  articles: Article[];
  forecasts: Forecast[];
};
export type Catalog = {
  events: { id: string; articles: Article[] }[];
  history: Article[];
  maps: { id: string; title: string; created_at: string }[];
  jobs: { id: string; map_id: string; title: string; stage: string; state: string; error: string | null }[];
};
export type Score = { count: number; brier: number | null; calibration: { predicted: number; observed: number; count: number }[] };
export type Metrics = {
  total: number; active: number; resolved: number; confirmed: number; refuted: number; inconclusive: number;
  resolution_rate: number | null; average_horizon_days: number | null; original: Score; revised_24h: Score;
  by_domain: Record<string, Score>; by_model: Record<string, Score>; revised_by_model: Record<string, Score>;
};
export type Infrastructure = {
  pending_jobs: number; failed_jobs: number;
  providers: { name: string; configured: boolean; model: string | null; reasoning_model: string | null;
    last_result: string | null; last_latency_ms: number | null; requests: number; failures: number;
    cache_hits: number; fallback_attempts: number; input_tokens: number | null; output_tokens: number | null; local_budget_remaining: number | null;
  }[];
};
export const label = (value: string) => value.replaceAll("_", " ");
export const day = (value: string) => value.slice(0, 10);
export const percent = (value: number) => `${(value * 100).toFixed(0)}%`;

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api/intelmap/${path}`, { cache: "no-store", ...options });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(typeof error?.detail === "string" ? error.detail : "Could not load IntelMap.");
  }
  return response.json();
}
