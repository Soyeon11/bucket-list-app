// Recommendation API functions mapping to /recommendations endpoints
import api from '@/services/api';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface RecommendationItemRef {
  id: string;
  title: string;
  category: string;
  priority: 'high' | 'medium' | 'low';
}

export interface ScoreBreakdown {
  priority_score: number;
  recency_bonus: number;
  season_score: number;
  weather_score: number;
}

export interface Recommendation {
  id: string;
  week_start: string;
  item: RecommendationItemRef;
  reason: string | null;
  score_breakdown: ScoreBreakdown | null;
  status: 'pending' | 'accepted' | 'skipped';
  accepted_at: string | null;
  skipped_at: string | null;
  created_at: string;
}

export interface RecommendationHistoryItem {
  id: string;
  week_start: string;
  item: RecommendationItemRef;
  status: 'pending' | 'accepted' | 'skipped';
  accepted_at: string | null;
}

export interface RecommendationHistory {
  data: RecommendationHistoryItem[];
  pagination: { page: number; limit: number; total: number; has_next: boolean };
}

// ─── API functions ────────────────────────────────────────────────────────────

/**
 * GET /recommendations/current — fetch this week's recommendation
 */
export async function getCurrentRecommendation(): Promise<Recommendation> {
  const { data } = await api.get<Recommendation>('/recommendations/current');
  return data;
}

/**
 * GET /recommendations/history — fetch paginated recommendation history
 */
export async function getRecommendationHistory(
  page = 1,
  limit = 10
): Promise<RecommendationHistory> {
  const { data } = await api.get<RecommendationHistory>('/recommendations/history', {
    params: { page, limit },
  });
  return data;
}

/**
 * POST /recommendations/{rec_id}/accept — accept this week's recommendation
 */
export async function acceptRecommendation(recId: string): Promise<void> {
  await api.post(`/recommendations/${recId}/accept`);
}

/**
 * POST /recommendations/{rec_id}/skip — skip this week's recommendation
 */
export async function skipRecommendation(recId: string): Promise<void> {
  await api.post(`/recommendations/${recId}/skip`);
}

/**
 * POST /recommendations/generate-now — trigger immediate recommendation generation
 */
export async function generateRecommendationNow(): Promise<Recommendation> {
  const { data } = await api.post<Recommendation>('/recommendations/generate-now');
  return data;
}
