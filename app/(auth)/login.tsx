// Login screen: social login buttons (Google / Apple) + email/password
import React, { useState } from 'react';
import { Alert, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { supabase } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleEmailLogin() {
    if (!email || !password) {
      Alert.alert('오류', '이메일과 비밀번호를 입력해주세요.');
      return;
    }
    setIsLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setIsLoading(false);
    if (error) Alert.alert('로그인 실패', error.message);
  }

  async function handleGoogleLogin() {
    // OAuth sign-in is handled via Supabase + Expo web browser
    const { error } = await supabase.auth.signInWithOAuth({ provider: 'google' });
    if (error) Alert.alert('Google 로그인 실패', error.message);
  }

  async function handleAppleLogin() {
    const { error } = await supabase.auth.signInWithOAuth({ provider: 'apple' });
    if (error) Alert.alert('Apple 로그인 실패', error.message);
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB' }}>
      <View style={{ flex: 1, paddingHorizontal: 24, justifyContent: 'center', gap: 24 }}>
        {/* Logo / heading */}
        <View className="items-center mb-4">
          <Text className="text-5xl mb-3">🪣</Text>
          <Text className="text-3xl font-bold text-gray-900">버킷리스트</Text>
          <Text className="text-sm text-gray-500 mt-1">매주 하나씩, 작은 도전을 시작하세요</Text>
        </View>

        {/* Social login */}
        <View className="gap-3">
          <Button
            label="Google로 계속하기"
            variant="secondary"
            fullWidth
            onPress={handleGoogleLogin}
          />
          <Button
            label="Apple로 계속하기"
            variant="secondary"
            fullWidth
            onPress={handleAppleLogin}
          />
        </View>

        {/* Divider */}
        <View className="flex-row items-center gap-3">
          <View className="flex-1 h-px bg-gray-200" />
          <Text className="text-sm text-gray-400">또는</Text>
          <View className="flex-1 h-px bg-gray-200" />
        </View>

        {/* Email / Password */}
        <View className="gap-4">
          <Input
            label="이메일"
            placeholder="example@email.com"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            returnKeyType="next"
          />
          <Input
            label="비밀번호"
            placeholder="비밀번호를 입력하세요"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            returnKeyType="done"
            onSubmitEditing={handleEmailLogin}
          />
          <Button
            label="로그인"
            variant="primary"
            fullWidth
            isLoading={isLoading}
            onPress={handleEmailLogin}
          />
        </View>

        <Text className="text-center text-sm text-gray-400">
          비밀번호를 잊으셨나요?{' '}
          <Text className="text-primary font-medium">재설정하기</Text>
        </Text>
      </View>
    </SafeAreaView>
  );
}
