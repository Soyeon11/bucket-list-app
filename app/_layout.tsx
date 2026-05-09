// Root layout: initializes Supabase auth session and wraps with QueryClient provider
import { useEffect } from 'react';
import { Stack, SplashScreen } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Session } from '@supabase/supabase-js';
import { supabase } from '@/services/api';
import { useUserStore } from '@/store/userStore';
import '../global.css';

// Keep splash screen visible until auth state resolves
SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 1000 * 60, // 1 minute global default
    },
  },
});

async function fetchProfile(session: Session, setProfile: ReturnType<typeof useUserStore.getState>['setProfile']) {
  const { data } = await supabase
    .from('profiles')
    .select('id, email, nickname, avatar_url, timezone')
    .eq('id', session.user.id)
    .single();
  if (data) setProfile(data as any);
}

export default function RootLayout() {
  const { setSession, setProfile, setLoading } = useUserStore();

  useEffect(() => {
    // Fetch initial session then load profile
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session) fetchProfile(session, setProfile);
      setLoading(false);
      SplashScreen.hideAsync();
    });

    // Subscribe to auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) fetchProfile(session, setProfile);
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <Stack screenOptions={{ headerShown: false }} />
    </QueryClientProvider>
  );
}
