// Bucket list screen: filterable FlatList with swipe-to-delete and FAB
import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Pressable,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { CATEGORIES, CategoryId } from '@/constants/categories';
import {
  useBucketList,
  useDeleteBucketItem,
  useCompleteBucketItem,
} from '@/hooks/useBucketList';
import { BucketItem } from '@/services/bucketlist';
import { BucketItemCard } from '@/components/BucketItem/BucketItemCard';
import { EmptyState } from '@/components/ui/EmptyState';

// Category filter tabs including "전체"
const FILTER_TABS = [{ id: 'all', label: '전체', emoji: '📋' }, ...CATEGORIES];

export default function BucketListScreen() {
  const [selectedCategory, setSelectedCategory] = useState<CategoryId | 'all'>('all');

  // Fetch items — pass category filter only when not "all"
  const { data, isLoading, isError, refetch, isFetching } = useBucketList({
    category: selectedCategory !== 'all' ? selectedCategory : undefined,
    status: 'active',
    limit: 50,
  });

  const deleteMutation = useDeleteBucketItem();
  const completeMutation = useCompleteBucketItem();

  const items = data?.data ?? [];

  // ─── Handlers ───────────────────────────────────────────────────────────────

  function handlePressItem(item: BucketItem) {
    router.push(`/item/${item.id}`);
  }

  function handleToggleComplete(item: BucketItem) {
    if (item.status === 'completed') return;
    Alert.alert(
      '완료 처리',
      `"${item.title}"을(를) 완료로 표시할까요?`,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '완료',
          onPress: () => completeMutation.mutate(item.id),
        },
      ]
    );
  }

  function handleDeleteItem(item: BucketItem) {
    Alert.alert(
      '아이템 삭제',
      `"${item.title}"을(를) 삭제할까요? 이 작업은 되돌릴 수 없습니다.`,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '삭제',
          style: 'destructive',
          onPress: () => deleteMutation.mutate(item.id),
        },
      ]
    );
  }

  const renderItem = useCallback(
    ({ item }: { item: BucketItem }) => (
      <View className="relative">
        {/* Swipe-to-delete: shown via long press → delete button */}
        <BucketItemCard
          item={item}
          onPress={() => handlePressItem(item)}
          onToggleComplete={() => handleToggleComplete(item)}
        />
        {/* Delete affordance via long press */}
        <Pressable
          accessibilityLabel={`${item.title} 삭제`}
          onPress={() => handleDeleteItem(item)}
          className="absolute right-4 top-4 p-1"
        >
          <Text className="text-gray-300 text-lg">⋯</Text>
        </Pressable>
      </View>
    ),
    [deleteMutation, completeMutation]
  );

  const renderEmpty = useCallback(() => {
    if (isLoading) return null;
    return (
      <EmptyState
        emoji="🪣"
        title="버킷리스트가 비어있어요"
        description="오른쪽 하단 + 버튼을 눌러 첫 번째 목표를 추가해보세요!"
      />
    );
  }, [isLoading]);

  // ─── Render ─────────────────────────────────────────────────────────────────

  if (isError) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB', alignItems: 'center', justifyContent: 'center' }}>
        <Text className="text-base text-gray-500 mb-4">데이터를 불러오지 못했어요.</Text>
        <Pressable onPress={() => refetch()} className="px-5 py-3 bg-primary rounded-xl">
          <Text className="text-white font-semibold">다시 시도</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB' }}>
      {/* Header */}
      <View className="px-4 pt-4 pb-2">
        <Text className="text-2xl font-bold text-gray-900">나의 버킷리스트</Text>
        <Text className="text-sm text-gray-500 mt-0.5">
          총 {data?.pagination?.total ?? 0}개의 목표
        </Text>
      </View>

      {/* Category filter tabs */}
      <FlatList
        horizontal
        data={FILTER_TABS}
        keyExtractor={tab => tab.id}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 8, gap: 8 }}
        renderItem={({ item: tab }) => {
          const isSelected = selectedCategory === tab.id;
          return (
            <Pressable
              accessibilityLabel={`${tab.label} 필터`}
              accessibilityRole="tab"
              accessibilityState={{ selected: isSelected }}
              onPress={() => setSelectedCategory(tab.id as CategoryId | 'all')}
              className={[
                'flex-row items-center rounded-full px-4 py-2',
                isSelected ? 'bg-primary' : 'bg-white border border-gray-200',
              ].join(' ')}
            >
              <Text className="mr-1 text-sm">{tab.emoji}</Text>
              <Text
                className={`text-sm font-medium ${isSelected ? 'text-white' : 'text-gray-600'}`}
              >
                {tab.label}
              </Text>
            </Pressable>
          );
        }}
      />

      {/* Items list */}
      {isLoading ? (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator size="large" color="#6366F1" />
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={item => item.id}
          renderItem={renderItem}
          ListEmptyComponent={renderEmpty}
          contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 8, flexGrow: 1 }}
          refreshing={isFetching && !isLoading}
          onRefresh={refetch}
          showsVerticalScrollIndicator={false}
        />
      )}

      {/* FAB: add new item */}
      <Pressable
        accessibilityLabel="새 버킷리스트 아이템 추가"
        accessibilityRole="button"
        onPress={() => router.push('/item/new')}
        className="absolute bottom-6 right-6 h-14 w-14 rounded-full bg-primary shadow-lg items-center justify-center active:bg-primary-600"
        style={{
          shadowColor: '#6366F1',
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.35,
          shadowRadius: 8,
          elevation: 8,
        }}
      >
        <Text className="text-3xl text-white leading-none">+</Text>
      </Pressable>
    </SafeAreaView>
  );
}
