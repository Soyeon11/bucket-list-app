// New item screen: form to create a new bucket list item
import React from 'react';
import { Alert, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, Stack } from 'expo-router';
import { useCreateBucketItem } from '@/hooks/useBucketList';
import { CreateItemPayload, UpdateItemPayload } from '@/services/bucketlist';
import { BucketItemForm } from '@/components/BucketItem/BucketItemForm';

export default function NewItemScreen() {
  const createMutation = useCreateBucketItem();

  async function handleSubmit(payload: CreateItemPayload | UpdateItemPayload) {
    try {
      await createMutation.mutateAsync(payload as CreateItemPayload);
      router.back();
    } catch {
      Alert.alert('오류', '아이템을 추가하지 못했어요. 다시 시도해주세요.');
    }
  }

  function handleCancel() {
    router.back();
  }

  return (
    <>
      <Stack.Screen
        options={{
          title: '새 버킷리스트 추가',
          headerShown: true,
          headerBackTitle: '목록',
        }}
      />
      <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB' }} edges={['bottom']}>
        <View className="flex-1">
          <BucketItemForm
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            isLoading={createMutation.isPending}
            submitLabel="추가하기"
          />
        </View>
      </SafeAreaView>
    </>
  );
}
