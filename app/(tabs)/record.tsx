// Record screen: select an active bucket list item to log activity
import React from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator } from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useBucketList } from '@/hooks/useBucketList';
import { BucketItemCard } from '@/components/BucketItem/BucketItemCard';

export default function RecordScreen() {
  const { data, isLoading } = useBucketList({ status: 'active' });
  const items = data?.data ?? [];

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="px-4 pt-4 pb-2">
        <Text className="text-2xl font-bold text-gray-900">실천 기록</Text>
        <Text className="text-sm text-gray-500 mt-1">
          아이템을 선택해서 기록을 남겨보세요
        </Text>
      </View>

      {isLoading ? (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator size="large" color="#6366f1" />
        </View>
      ) : items.length === 0 ? (
        <View className="flex-1 items-center justify-center px-8">
          <Text className="text-gray-400 text-center">
            진행 중인 버킷리스트 아이템이 없어요.{'\n'}먼저 아이템을 추가해보세요!
          </Text>
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ padding: 16 }}
          renderItem={({ item }) => (
            <TouchableOpacity onPress={() => router.push(`/item/${item.id}`)}>
              <BucketItemCard item={item} />
            </TouchableOpacity>
          )}
        />
      )}
    </SafeAreaView>
  );
}
