// TanStack Query hooks for recommendation data fetching and mutations
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getCurrentRecommendation,
  getRecommendationHistory,
  acceptRecommendation,
  skipRecommendation,
  generateRecommendationNow,
} from '@/services/recommendations';

// ─── Query keys ───────────────────────────────────────────────────────────────

export const recommendationKeys = {
  all: ['recommendation'] as const,
  current: () => [...recommendationKeys.all, 'current'] as const,
  history: (page: number) => [...recommendationKeys.all, 'history', page] as const,
};

// ─── Read hooks ───────────────────────────────────────────────────────────────

/**
 * Fetch the current week's recommendation.
 * Stale after 30 minutes to reduce unnecessary refetches.
 */
export function useCurrentRecommendation() {
  return useQuery({
    queryKey: recommendationKeys.current(),
    queryFn: getCurrentRecommendation,
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
}

/**
 * Fetch paginated recommendation history.
 */
export function useRecommendationHistory(page: number) {
  return useQuery({
    queryKey: recommendationKeys.history(page),
    queryFn: () => getRecommendationHistory(page),
  });
}

// ─── Mutation hooks ───────────────────────────────────────────────────────────

/**
 * Accept the current week's recommendation.
 * Invalidates current recommendation on success.
 */
export function useAcceptRecommendation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (recId: string) => acceptRecommendation(recId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: recommendationKeys.current() });
    },
  });
}

/**
 * Skip the current week's recommendation.
 * Invalidates current recommendation on success.
 */
export function useSkipRecommendation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (recId: string) => skipRecommendation(recId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: recommendationKeys.current() });
    },
  });
}

/**
 * Trigger immediate recommendation generation.
 * Invalidates current recommendation on success.
 */
export function useGenerateRecommendation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: generateRecommendationNow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: recommendationKeys.current() });
    },
  });
}
