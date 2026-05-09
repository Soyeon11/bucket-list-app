// Weekly recommendation card for home screen
import React from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Recommendation } from '@/services/recommendations';
import { CATEGORY_MAP } from '@/constants/categories';

interface RecommendationCardProps {
  recommendation: Recommendation | null | undefined;
  isLoading: boolean;
  onAccept: () => void;
  onSkip: () => void;
}

function getTotalScore(sb: Recommendation['score_breakdown']): number {
  if (!sb) return 0;
  return sb.priority_score + sb.recency_bonus + sb.season_score + sb.weather_score;
}

function getCategoryEmoji(category: string): string {
  const cat = CATEGORY_MAP[category as keyof typeof CATEGORY_MAP];
  return cat?.emoji ?? '🎯';
}

export function RecommendationCard({
  recommendation,
  isLoading,
  onAccept,
  onSkip,
}: RecommendationCardProps) {
  // Loading state
  if (isLoading) {
    return (
      <View style={styles.card}>
        <View style={[styles.shimmerBadge, styles.shimmer]} />
        <View style={[styles.shimmerTitle, styles.shimmer]} />
        <View style={[styles.shimmerTitleShort, styles.shimmer]} />
        <View style={[styles.shimmerReason, styles.shimmer]} />
      </View>
    );
  }

  // Null / empty state
  if (!recommendation) {
    return (
      <View style={styles.emptyCard}>
        <Text style={styles.emptyEmoji}>🪣</Text>
        <Text style={styles.emptyTitle}>아직 추천이 없어요</Text>
        <Text style={styles.emptySubtitle}>
          버킷리스트 아이템을 추가하면 추천이 시작돼요!
        </Text>
      </View>
    );
  }

  // Status badge label
  const badgeLabel =
    recommendation.status === 'accepted'
      ? '✓ 수락됨'
      : recommendation.status === 'skipped'
        ? '건너뜀'
        : '이번 주 추천';

  const totalScore = getTotalScore(recommendation.score_breakdown);
  const categoryEmoji = getCategoryEmoji(recommendation.item.category);

  return (
    <View style={styles.card}>
      {/* Status badge */}
      <View style={styles.badgeRow}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{badgeLabel}</Text>
        </View>
        {recommendation.score_breakdown && (
          <Text style={styles.scoreText}>점수: {totalScore}점</Text>
        )}
      </View>

      {/* Title */}
      <Text style={styles.title}>
        {categoryEmoji} {recommendation.item.title}
      </Text>

      {/* Reason */}
      {recommendation.reason ? (
        <Text style={styles.reason}>{recommendation.reason}</Text>
      ) : null}

      {/* Action buttons — only shown when pending */}
      {recommendation.status === 'pending' && (
        <View style={styles.buttonRow}>
          <TouchableOpacity style={styles.acceptButton} onPress={onAccept} activeOpacity={0.8}>
            <Text style={styles.acceptButtonText}>수락하기</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.skipButton} onPress={onSkip} activeOpacity={0.8}>
            <Text style={styles.skipButtonText}>다음 주로 미루기</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const CARD_BG = '#6366F1';

const styles = StyleSheet.create({
  // Normal card
  card: {
    backgroundColor: CARD_BG,
    borderRadius: 24,
    padding: 24,
    gap: 12,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  badge: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  scoreText: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.7)',
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#FFFFFF',
    lineHeight: 30,
  },
  reason: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.75)',
    lineHeight: 20,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  acceptButton: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    paddingVertical: 12,
    alignItems: 'center',
  },
  acceptButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: CARD_BG,
  },
  skipButton: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: 14,
    paddingVertical: 12,
    alignItems: 'center',
  },
  skipButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },

  // Loading shimmer placeholders
  shimmer: {
    backgroundColor: 'rgba(255,255,255,0.5)',
    borderRadius: 8,
  },
  shimmerBadge: {
    height: 24,
    width: 100,
    borderRadius: 999,
  },
  shimmerTitle: {
    height: 28,
    width: '90%',
  },
  shimmerTitleShort: {
    height: 28,
    width: '60%',
  },
  shimmerReason: {
    height: 16,
    width: '80%',
    marginTop: 4,
  },

  // Empty state
  emptyCard: {
    backgroundColor: CARD_BG,
    borderRadius: 24,
    padding: 32,
    alignItems: 'center',
    gap: 8,
  },
  emptyEmoji: {
    fontSize: 40,
    marginBottom: 4,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  emptySubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.75)',
    textAlign: 'center',
    lineHeight: 20,
  },
});
