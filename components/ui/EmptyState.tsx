// Empty state placeholder component
import React from 'react';
import { Text, View } from 'react-native';
import { Button } from './Button';

interface EmptyStateProps {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  emoji?: string;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  emoji = '📋',
}: EmptyStateProps) {
  return (
    <View className="flex-1 items-center justify-center px-8 py-16">
      <Text className="mb-4 text-6xl">{emoji}</Text>
      <Text className="mb-2 text-center text-xl font-bold text-gray-800">{title}</Text>
      {description && (
        <Text className="mb-6 text-center text-sm text-gray-500">{description}</Text>
      )}
      {actionLabel && onAction && (
        <Button label={actionLabel} onPress={onAction} variant="primary" />
      )}
    </View>
  );
}
