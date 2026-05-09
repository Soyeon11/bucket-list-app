// Card component for displaying a bucket list item in a list
import React from 'react';
import { Pressable, Text, View } from 'react-native';
import { BucketItem } from '@/services/bucketlist';
import { CATEGORY_MAP, PRIORITY_MAP } from '@/constants/categories';

interface BucketItemCardProps {
  item: BucketItem;
  onPress?: () => void;
  onToggleComplete?: () => void;
}

export function BucketItemCard({ item, onPress, onToggleComplete }: BucketItemCardProps) {
  const category = CATEGORY_MAP[item.category];
  const priority = PRIORITY_MAP[item.priority];
  const isCompleted = item.status === 'completed';

  return (
    <Pressable
      accessibilityLabel={`버킷리스트 아이템: ${item.title}`}
      accessibilityRole="button"
      onPress={onPress}
      className="mb-3 rounded-2xl bg-white p-4 shadow-sm border border-gray-100 active:bg-gray-50"
    >
      <View className="flex-row items-start justify-between">
        {/* Left: checkbox + content */}
        <View className="flex-1 flex-row items-start gap-3">
          {/* Completion checkbox */}
          <Pressable
            accessibilityLabel={isCompleted ? '완료 취소' : '완료로 표시'}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: isCompleted }}
            onPress={e => {
              e.stopPropagation?.();
              onToggleComplete?.();
            }}
            className={[
              'mt-0.5 h-6 w-6 rounded-full border-2 items-center justify-center',
              isCompleted
                ? 'bg-primary border-primary'
                : 'border-gray-300 bg-white',
            ].join(' ')}
          >
            {isCompleted && (
              <Text className="text-xs text-white font-bold">✓</Text>
            )}
          </Pressable>

          {/* Title and meta */}
          <View className="flex-1">
            <Text
              className={[
                'text-base font-semibold',
                isCompleted ? 'text-gray-400 line-through' : 'text-gray-900',
              ].join(' ')}
              numberOfLines={2}
            >
              {item.title}
            </Text>

            {item.description ? (
              <Text className="mt-1 text-sm text-gray-500" numberOfLines={2}>
                {item.description}
              </Text>
            ) : null}

            {/* Badges row */}
            <View className="mt-2 flex-row items-center gap-2 flex-wrap">
              {/* Category badge */}
              {category && (
                <View
                  className="rounded-full px-2 py-0.5 flex-row items-center"
                  style={{ backgroundColor: `${category.color}20` }}
                >
                  <Text className="text-xs mr-1">{category.emoji}</Text>
                  <Text className="text-xs font-medium" style={{ color: category.color }}>
                    {category.label}
                  </Text>
                </View>
              )}

              {/* Priority badge */}
              {priority && (
                <View
                  className="rounded-full px-2 py-0.5"
                  style={{ backgroundColor: `${priority.color}20` }}
                >
                  <Text className="text-xs font-medium" style={{ color: priority.color }}>
                    {priority.label}
                  </Text>
                </View>
              )}
            </View>
          </View>
        </View>

        {/* Right: priority indicator bar */}
        <View className="ml-2 flex-col items-center gap-0.5">
          {[1, 2, 3].map(level => {
            const filled =
              (item.priority === 'high' && level <= 3) ||
              (item.priority === 'medium' && level <= 2) ||
              (item.priority === 'low' && level <= 1);

            return (
              <View
                key={level}
                className="w-1.5 h-3 rounded-full"
                style={{
                  backgroundColor: filled ? priority?.color ?? '#6366F1' : '#E5E7EB',
                }}
              />
            );
          })}
        </View>
      </View>
    </Pressable>
  );
}
