// Zustand store for user authentication state
import { create } from 'zustand';
import { Session, User } from '@supabase/supabase-js';

interface UserProfile {
  id: string;
  email: string;
  nickname: string;
  avatar_url: string | null;
  timezone: string;
  stats: {
    total_items: number;
    completed_items: number;
    total_videos: number;
  };
}

interface UserState {
  // Auth
  session: Session | null;
  user: User | null;
  profile: UserProfile | null;
  isLoading: boolean;

  // Actions
  setSession: (session: Session | null) => void;
  setProfile: (profile: UserProfile | null) => void;
  setLoading: (loading: boolean) => void;
  clearUser: () => void;
}

export const useUserStore = create<UserState>(set => ({
  session: null,
  user: null,
  profile: null,
  isLoading: true,

  setSession: session =>
    set({
      session,
      user: session?.user ?? null,
    }),

  setProfile: profile => set({ profile }),

  setLoading: isLoading => set({ isLoading }),

  clearUser: () =>
    set({
      session: null,
      user: null,
      profile: null,
    }),
}));
