import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { AuthState } from '@/types/auth.types';
import { authApi } from '@/api/authApi';

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      initialize: async () => {
        try {
          set({ isLoading: true });
          const userData = localStorage.getItem('user');
          if (userData) {
            const user = JSON.parse(userData);
            // Verify token is still valid
            await authApi.getProfile();
            set({ user, isAuthenticated: true });
          }
        } catch (error) {
          localStorage.removeItem('user');
          set({ user: null, isAuthenticated: false });
        } finally {
          set({ isLoading: false });
        }
      },

      login: async (email: string, password: string) => {
        try {
          set({ isLoading: true, error: null });
          const { data } = await authApi.login({ email, password });
          localStorage.setItem('user', JSON.stringify(data.user));
          set({ user: data.user, isAuthenticated: true });
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Login failed';
          set({ error: errorMessage });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      socialLogin: async (provider: 'google' | 'github', code: string) => {
        try {
          set({ isLoading: true, error: null });
          const { data } = await authApi.socialLogin(provider, code);
          localStorage.setItem('user', JSON.stringify(data.user));
          set({ user: data.user, isAuthenticated: true });
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Social login failed';
          set({ error: errorMessage });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      logout: async () => {
        try {
          set({ isLoading: true });
          await authApi.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          localStorage.removeItem('user');
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      setError: (error: string | null) => set({ error }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
