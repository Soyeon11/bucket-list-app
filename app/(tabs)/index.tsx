// Home screen: weekly recommendation card + in-progress items summary
import React from 'react';
import { Alert, ScrollView, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { useUserStore } from '@/store/userStore';
import { supabase } from '@/services/api';
import { RecommendationCard } from '@/components/Recommendation/RecommendationCard';
import {
  useCurrentRecommendation,
  useAcceptRecommendation,
  useSkipRecommendation,
} from '@/hooks/useRecommendation';

export default function HomeScreen() {
  const { profile, clearUser } = useUserStore();
  const nickname = profile?.nickname ?? '사용자';

  const { data: recommendation, isLoading } = useCurrentRecommendation();
  const acceptMutation = useAcceptRecommendation();
  const skipMutation = useSkipRecommendation();

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

  function handleAccept() {
    if (!recommendation) return;
    acceptMutation.mutate(recommendation.id);
  }

  function handleSkip() {
    if (!recommendation) return;
    skipMutation.mutate(recommendation.id);
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB' }}>
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 24, gap: 20 }}
      >
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

        {/* Weekly recommendation card */}
        <RecommendationCard
          recommendation={recommendation}
          isLoading={isLoading}
          onAccept={handleAccept}
          onSkip={handleSkip}
        />

        {/* History link */}
        <TouchableOpacity
          onPress={() => router.push('/recommendations/history')}
          style={{ alignItems: 'center', paddingVertical: 4 }}
        >
          <Text style={{ fontSize: 14, color: '#6366F1', fontWeight: '600' }}>
            추천 기록 보기 →
          </Text>
        </TouchableOpacity>

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
