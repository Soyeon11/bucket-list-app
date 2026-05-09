// Home screen: weekly recommendation placeholder card + in-progress items summary
import React from 'react';
import { Alert, ScrollView, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useUserStore } from '@/store/userStore';
import { supabase } from '@/services/api';
import { Button } from '@/components/ui/Button';

export default function HomeScreen() {
  const { profile, clearUser } = useUserStore();
  const nickname = profile?.nickname ?? '사용자';

  async function handleLogout() {
    Alert.alert('로그아웃', '정말 로그아웃 하시겠어요?', [
      { text: '취소', style: 'cancel' },
      {
        text: '로그아웃',
        style: 'destructive',
        onPress: async () => {
          await supabase.auth.signOut();
          clearUser();
        },
      },
    ]);
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB' }}>
      <ScrollView style={{ flex: 1 }} contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 24, gap: 20 }}>
        {/* Header greeting */}
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <View>
            <Text className="text-2xl font-bold text-gray-900">
              안녕하세요, {nickname}님 👋
            </Text>
            <Text className="text-sm text-gray-500 mt-1">오늘의 도전을 시작해보세요!</Text>
          </View>
          <TouchableOpacity onPress={handleLogout} style={{ paddingTop: 4 }}>
            <Text style={{ fontSize: 13, color: '#9CA3AF' }}>로그아웃</Text>
          </TouchableOpacity>
        </View>

        {/* Weekly recommendation placeholder card */}
        <View className="rounded-3xl bg-primary p-6 gap-4">
          <View className="flex-row items-center gap-2">
            <View className="rounded-full bg-white/20 px-3 py-1">
              <Text className="text-xs font-medium text-white">이번 주 추천</Text>
            </View>
          </View>
          <Text className="text-xl font-bold text-white">
            이번 주의 버킷리스트를{'\n'}불러오는 중...
          </Text>
          <Text className="text-sm text-white/70">
            이번 주 날씨와 당신의 우선순위를 고려했어요
          </Text>
          <View className="flex-row gap-3 mt-2">
            <Button label="수락" variant="ghost" />
            <Button label="다음 주로 미루기" variant="ghost" />
          </View>
        </View>

        {/* In-progress items section */}
        <View className="gap-3">
          <Text className="text-lg font-bold text-gray-900">진행 중인 도전</Text>
          <View className="rounded-2xl bg-white border border-gray-100 p-6 items-center">
            <Text className="text-4xl mb-3">🎯</Text>
            <Text className="text-base font-semibold text-gray-700">
              버킷리스트를 추가하고 도전을 시작하세요!
            </Text>
            <Text className="text-sm text-gray-400 mt-1 text-center">
              하단의 버킷리스트 탭에서 목표를 추가할 수 있어요
            </Text>
          </View>
        </View>

        {/* Monthly achievement badges placeholder */}
        <View className="gap-3">
          <Text className="text-lg font-bold text-gray-900">이번 달 달성 배지</Text>
          <View className="rounded-2xl bg-white border border-gray-100 p-4 flex-row gap-3">
            {['🥇', '🌟', '🏆'].map((emoji, i) => (
              <View key={i} className="items-center gap-1 opacity-30">
                <Text className="text-3xl">{emoji}</Text>
                <View className="w-8 h-1.5 rounded-full bg-gray-200" />
              </View>
            ))}
            <View className="flex-1 items-center justify-center">
              <Text className="text-xs text-gray-400">도전을 완료하면{'\n'}배지를 얻어요!</Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
