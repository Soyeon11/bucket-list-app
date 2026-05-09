// Auth flow layout: redirect to tabs if already authenticated
import { Redirect, Stack } from 'expo-router';
import { useUserStore } from '@/store/userStore';

export default function AuthLayout() {
  const { session, isLoading } = useUserStore();

  // Wait for auth state to resolve
  if (isLoading) return null;

  // Already logged in → go to main app
  if (session) return <Redirect href="/(tabs)" />;

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="login" />
    </Stack>
  );
}
