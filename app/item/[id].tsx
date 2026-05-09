// Item detail screen: view, edit, and log activity for a bucket list item
import React, { useState } from 'react';
import { ActivityIndicator, Alert, Image, Modal, ScrollView, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, Stack, useLocalSearchParams } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
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
import { useActivityLogs, useCreateLog } from '@/hooks/useActivityLog';
import LogCard from '@/components/ActivityLog/LogCard';

export default function ItemDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [isEditing, setIsEditing] = useState(false);
  const [showLogModal, setShowLogModal] = useState(false);
  const [logNote, setLogNote] = useState('');
  const [selectedMedia, setSelectedMedia] = useState<ImagePicker.ImagePickerAsset[]>([]);
  const [isSubmittingLog, setIsSubmittingLog] = useState(false);

  const { data: item, isLoading, isError } = useBucketItem(id ?? '');
  const updateMutation = useUpdateBucketItem();
  const deleteMutation = useDeleteBucketItem();
  const completeMutation = useCompleteBucketItem();
  const { data: logsData, isLoading: isLogsLoading } = useActivityLogs(id as string);
  const createLog = useCreateLog();

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

  const handlePickMedia = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.All,
      allowsMultipleSelection: true,
      quality: 0.8,
      selectionLimit: 10,
    });
    if (!result.canceled) {
      setSelectedMedia((prev) => [...prev, ...result.assets].slice(0, 10));
    }
  };

  const handleSubmitLog = async () => {
    if (!id) return;
    setIsSubmittingLog(true);
    try {
      await createLog.mutateAsync({
        itemId: id as string,
        payload: { note: logNote.trim() || null },
        mediaFiles: selectedMedia.map((asset, idx) => ({
          uri: asset.uri,
          filename: asset.fileName ?? `media_${idx + 1}.${asset.type === 'video' ? 'mp4' : 'jpg'}`,
          mimeType: asset.mimeType ?? (asset.type === 'video' ? 'video/mp4' : 'image/jpeg'),
          fileSize: asset.fileSize ?? 0,
        })),
      });
      setLogNote('');
      setSelectedMedia([]);
      setShowLogModal(false);
    } catch {
      Alert.alert('오류', '기록 저장에 실패했어요. 다시 시도해주세요.');
    } finally {
      setIsSubmittingLog(false);
    }
  };

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
          <View className="gap-3">
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

          {/* Activity Logs Section */}
          <View className="mt-6 mb-4">
            <View className="flex-row justify-between items-center mb-3">
              <Text className="text-lg font-semibold text-gray-900">실천 기록</Text>
              <TouchableOpacity
                onPress={() => setShowLogModal(true)}
                className="bg-indigo-500 px-3 py-1.5 rounded-lg"
              >
                <Text className="text-white text-sm font-medium">+ 기록 추가</Text>
              </TouchableOpacity>
            </View>

            {isLogsLoading ? (
              <ActivityIndicator size="small" color="#6366f1" />
            ) : !logsData?.data?.length ? (
              <Text className="text-gray-400 text-sm text-center py-4">
                아직 기록이 없어요. 첫 번째 기록을 남겨보세요!
              </Text>
            ) : (
              logsData.data.map((log) => (
                <LogCard key={log.id} log={log} />
              ))
            )}
          </View>
        </ScrollView>

        {/* Log Creation Modal */}
        <Modal
          visible={showLogModal}
          animationType="slide"
          presentationStyle="pageSheet"
          onRequestClose={() => setShowLogModal(false)}
        >
          <SafeAreaView className="flex-1 bg-white">
            <View className="flex-row justify-between items-center px-4 py-3 border-b border-gray-100">
              <TouchableOpacity onPress={() => setShowLogModal(false)}>
                <Text className="text-gray-500">취소</Text>
              </TouchableOpacity>
              <Text className="font-semibold text-gray-900">기록 추가</Text>
              <TouchableOpacity onPress={handleSubmitLog} disabled={isSubmittingLog}>
                <Text className={`font-semibold ${isSubmittingLog ? 'text-gray-300' : 'text-indigo-500'}`}>
                  저장
                </Text>
              </TouchableOpacity>
            </View>

            <ScrollView className="flex-1 px-4 py-4">
              <Text className="text-sm font-medium text-gray-700 mb-2">노트 (선택)</Text>
              <TextInput
                value={logNote}
                onChangeText={setLogNote}
                placeholder="오늘의 기록을 남겨보세요..."
                multiline
                numberOfLines={4}
                className="border border-gray-200 rounded-xl p-3 text-gray-700 min-h-[100px]"
                textAlignVertical="top"
              />

              <View className="mt-4">
                <Text className="text-sm font-medium text-gray-700 mb-2">
                  미디어 ({selectedMedia.length}/10)
                </Text>
                <TouchableOpacity
                  onPress={handlePickMedia}
                  className="border-2 border-dashed border-gray-300 rounded-xl p-4 items-center"
                >
                  <Text className="text-gray-500 text-sm">사진/동영상 추가</Text>
                </TouchableOpacity>

                {selectedMedia.length > 0 && (
                  <View className="flex-row flex-wrap gap-1 mt-2">
                    {selectedMedia.map((asset, idx) => (
                      <View key={idx} className="w-[31%] aspect-square bg-gray-200 rounded-lg overflow-hidden">
                        <Image source={{ uri: asset.uri }} className="w-full h-full" resizeMode="cover" />
                        <TouchableOpacity
                          onPress={() => setSelectedMedia((prev) => prev.filter((_, i) => i !== idx))}
                          className="absolute top-1 right-1 bg-black/60 rounded-full w-5 h-5 items-center justify-center"
                        >
                          <Text className="text-white text-xs">✕</Text>
                        </TouchableOpacity>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            </ScrollView>
          </SafeAreaView>
        </Modal>
      </SafeAreaView>
    </>
  );
}
