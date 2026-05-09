// History list item component for recommendation history screen
import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { RecommendationHistoryItem } from '@/services/recommendations';
import { CATEGORY_MAP } from '@/constants/categories';

interface HistoryItemProps {
  item: RecommendationHistoryItem;
  onPress: () => void;
}

function formatWeekStart(dateStr: string): string {
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  return `${year}년 ${month}월 ${day}일 주차`;
}

function getCategoryEmoji(category: string): string {
  const cat = CATEGORY_MAP[category as keyof typeof CATEGORY_MAP];
  return cat?.emoji ?? '🎯';
}

const STATUS_CONFIG = {
  accepted: { label: '수락됨', color: '#10B981', bg: '#D1FAE5' },
  skipped: { label: '건너뜀', color: '#6B7280', bg: '#F3F4F6' },
  pending: { label: '대기중', color: '#F59E0B', bg: '#FEF3C7' },
} as const;

export function HistoryItem({ item, onPress }: HistoryItemProps) {
  const status = STATUS_CONFIG[item.status] ?? STATUS_CONFIG.pending;
  const emoji = getCategoryEmoji(item.item.category);

  return (
    <TouchableOpacity style={styles.container} onPress={onPress} activeOpacity={0.7}>
      {/* Category emoji */}
      <View style={styles.emojiContainer}>
        <Text style={styles.emoji}>{emoji}</Text>
      </View>

      {/* Content */}
      <View style={styles.content}>
        <Text style={styles.weekLabel}>{formatWeekStart(item.week_start)}</Text>
        <Text style={styles.title} numberOfLines={2}>
          {item.item.title}
        </Text>
      </View>

      {/* Status badge */}
      <View style={[styles.badge, { backgroundColor: status.bg }]}>
        <Text style={[styles.badgeText, { color: status.color }]}>{status.label}</Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    gap: 12,
    borderWidth: 1,
    borderColor: '#F3F4F6',
  },
  emojiContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#F9FAFB',
    alignItems: 'center',
    justifyContent: 'center',
  },
  emoji: {
    fontSize: 22,
  },
  content: {
    flex: 1,
    gap: 2,
  },
  weekLabel: {
    fontSize: 11,
    color: '#9CA3AF',
    fontWeight: '500',
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    lineHeight: 20,
  },
  badge: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
  },
});
