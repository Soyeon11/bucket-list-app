// Record screen placeholder — Phase 2 implementation
import React from 'react';
import { Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function RecordScreen() {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB' }}>
      <View style={{ paddingHorizontal: 16, paddingTop: 16, paddingBottom: 8 }}>
        <Text className="text-2xl font-bold text-gray-900">기록</Text>
      </View>
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 32 }}>
        <Text className="text-5xl mb-4">📸</Text>
        <Text className="text-xl font-bold text-gray-800 mb-2">기록 화면</Text>
        <Text className="text-sm text-gray-500 text-center">
          Phase 2에서 구현 예정입니다.{'\n'}
          사진/영상 업로드와 활동 기록을 남길 수 있어요.
        </Text>
      </View>
    </SafeAreaView>
  );
}
