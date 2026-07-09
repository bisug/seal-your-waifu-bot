import { create } from 'zustand';
import { type User } from '../context/UserContext';
import { apiFetch, getErrorMessage } from '../api/client';

interface UserState {
  user: User | null;
  loading: boolean;
  error: string | null;
  liteMode: boolean;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  toggleLiteMode: () => void;
  fetchUser: () => Promise<void>;
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  loading: true,
  error: null,
  liteMode: true,
  setUser: (user) => set({ user }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  toggleLiteMode: () => set((state) => ({ liteMode: !state.liteMode })),
  fetchUser: async () => {
    set({ loading: true });
    try {
      const data = await apiFetch('/me');
      set({ user: data, error: null });
    } catch (err: any) {
      set({ error: getErrorMessage(err) });
    } finally {
      set({ loading: false });
    }
  },
}));
