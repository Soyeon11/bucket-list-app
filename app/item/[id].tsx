// Item detail screen: view and edit a bucket list item
import React, { useState } from 'react';
import { ActivityIndicator, Alert, ScrollView, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, Stack, useLocalSearchParams } from 'expo-router';
import {
  useBucketItem,
  useUpdateBucketItem,
  useDeleteBucketItem,
  useCompleteBucketItem,
} from '@/hooks/useBucketList';
import { UpdateItemPayload } from '@/services/bucketlist';
import { BucketItemForm } from '@/components/BucketItem/BucketItemForm';
import { Button } from '@/components/ui/Button';
import { CATEGORY_MAP, PRIORITY_MAP } from '@/constants/categories';

export default function ItemDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [isEditing, setIsEditing] = useState(false);

  const { data: item, isLoading, isError } = useBucketItem(id ?? '');
  const updateMutation = useUpdateBucketItem();
  const deleteMutation = useDeleteBucketItem();
  const completeMutation = useCompleteBucketItem();

  // ─── Handlers ───────────────────────────────────────────────────────────────

  async function handleUpdate(payload: UpdateItemPayload) {
    if (!id) return;
    try {
      await updateMutation.mutateAsync({ itemId: id, payload });
      setIsEditing(false);
    } catch {
      Alert.alert('오류', '아이템을 수정하지 못했어요. 다시 시도해주세요.');
    }
  }

  function handleDelete() {
    if (!id || !item) return;
    Alert.alert(
      '아이템 삭제',
      `"${item.title}"을(를) 삭제할까요?`,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '삭제',
          style: 'destructive',
          onPress: async () => {
            await deleteMutation.mutateAsync(id);
            router.back();
          },
        },
      ]
    );
  }

  function handleComplete() {
    if (!id || !item) return;
    Alert.alert(
      '완료 처리',
      `"${item.title}"을(를) 완료로 표시할까요?`,
      [
        { text: '취소', style: 'cancel' },
        { text: '완료', onPress: () => completeMutation.mutate(id) },
      ]
    );
  }

  // ─── Loading / Error states ──────────────────────────────────────────────────

  if (isLoading) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB', alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator size="large" color="#6366F1" />
      </SafeAreaView>
    );
  }

  if (isError || !item) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB', alignItems: 'center', justifyContent: 'center', paddingHorizontal: 32 }}>
        <Text className="text-base text-gray-500 mb-4 text-center">
          아이템을 불러오지 못했어요.
        </Text>
        <Button label="돌아가기" onPress={() => router.back()} />
      </SafeAreaView>
    );
  }

  const category = CATEGORY_MAP[item.category];
  const priority = PRIORITY_MAP[item.priority];

  // ─── Edit mode ───────────────────────────────────────────────────────────────

  if (isEditing) {
    return (
      <>
        <Stack.Screen options={{ title: '아이템 수정', headerShown: true, headerBackTitle: '취소' }} />
        <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB' }} edges={['bottom']}>
          <BucketItemForm
            initialValues={{
              title: item.title,
              category: item.category,
              priority: item.priority,
              description: item.description ?? '',
              tags: item.tags,
            }}
            onSubmit={handleUpdate}
            onCancel={() => setIsEditing(false)}
            isLoading={updateMutation.isPending}
            submitLabel="저장하기"
          />
        </SafeAreaView>
      </>
    );
  }

  // ─── View mode ───────────────────────────────────────────────────────────────

  return (
    <>
      <Stack.Screen
        options={{
          title: '아이템 상세',
          headerShown: true,
          headerBackTitle: '목록',
          headerRight: () => (
            <TouchableOpacity
              accessibilityLabel="수정"
              onPress={() => setIsEditing(true)}
              className="px-2"
            >
              <Text className="text-primary font-semibold">수정</Text>
            </TouchableOpacity>
          ),
        }}
      />
      <SafeAreaView className="flex-1 bg-surface" edges={['bottom']}>
        <ScrollView style={{ flex: 1 }} contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 24, gap: 20 }}>
          {/* Title + status */}
          <View className="gap-2">
            <Text className="text-2xl font-bold text-gray-900">{item.title}</Text>
            {item.status === 'completed' && (
              <View className="flex-row items-center gap-1">
                <Text className="text-green-500 text-sm font-medium">✓ 완료됨</Text>
                {item.completed_at && (
                  <Text className="text-gray-400 text-xs">
                    {new Date(item.completed_at).toLocaleDateString('ko-KR')}
                  </Text>
                )}
              </View>
            )}
          </View>

          {/* Badges */}
          <View className="flex-row gap-2 flex-wrap">
            {category && (
              <View
                className="flex-row items-center rounded-full px-3 py-1.5"
                style={{ backgroundColor: `${category.color}20` }}
              >
                <Text className="mr-1">{category.emoji}</Text>
                <Text className="text-sm font-medium" style={{ color: category.color }}>
                  {category.label}
                </Text>
              </View>
            )}
            {priority && (
              <View
                className="rounded-full px-3 py-1.5"
                style={{ backgroundColor: `${priority.color}20` }}
              >
                <Text className="text-sm font-medium" style={{ color: priority.color }}>
                  우선순위 {priority.label}
                </Text>
              </View>
            )}
          </View>

          {/* Description */}
          {item.description ? (
            <View className="rounded-2xl bg-white border border-gray-100 p-4">
              <Text className="text-sm font-medium text-gray-500 mb-2">설명</Text>
              <Text className="text-base text-gray-800 leading-relaxed">{item.description}</Text>
            </View>
          ) : null}

          {/* Tags */}
          {item.tags.length > 0 && (
            <View>
              <Text className="text-sm font-medium text-gray-500 mb-2">태그</Text>
              <View className="flex-row flex-wrap gap-2">
                {item.tags.map(tag => (
                  <View key={tag} className="rounded-full bg-gray-100 px-3 py-1">
                    <Text className="text-sm text-gray-700">#{tag}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Metadata */}
          <View className="rounded-2xl bg-white border border-gray-100 p-4 gap-2">
            <Text className="text-sm font-medium text-gray-500 mb-1">정보</Text>
            <View className="flex-row justify-between">
              <Text className="text-sm text-gray-500">생성일</Text>
              <Text className="text-sm text-gray-700">
                {new Date(item.created_at).toLocaleDateString('ko-KR')}
              </Text>
            </View>
            {item.logs_count !== undefined && (
              <View className="flex-row justify-between">
                <Text className="text-sm text-gray-500">기록 수</Text>
                <Text className="text-sm text-gray-700">{item.logs_count}개</Text>
              </View>
            )}
          </View>

          {/* Action buttons */}
          <View className="gap-3 pb-4">
            {item.status !== 'completed' && (
              <Button
                label="완료로 표시"
                variant="primary"
                fullWidth
                isLoading={completeMutation.isPending}
                onPress={handleComplete}
              />
            )}
            <Button
              label="삭제하기"
              variant="danger"
              fullWidth
              isLoading={deleteMutation.isPending}
              onPress={handleDelete}
            />
          </View>
        </ScrollView>
      </SafeAreaView>
    </>
  );
}
