import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getProfile, logout, loginWithGoogle, loginWithGithub } from '@/api/apiFunctions';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import type { User } from '@/types/auth.types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  socialLogin: (provider: 'google' | 'github', code: string) => Promise<void>;
  logoutUser: () => Promise<void>;
  setError: (msg: string | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const initialize = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {      
      const response = await getProfile();
      
      if (response?.user) {
        setUser(response.user);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (e) {
      setUser(null);
      setIsAuthenticated(false);
      console.error('Auth initialization failed:', e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    initialize();
  }, [initialize]);

const socialLogin = useCallback(async (provider: 'google' | 'github', code: string) => {
  setIsLoading(true);
  setError(null);

  try {
    let response;

    if (provider === 'google') {
      response = await loginWithGoogle(code);
    } else if (provider === 'github') {
      response = await loginWithGithub(code);
    } else {
      throw new Error(`Unsupported provider: ${provider}`);
    }

    if (!response?.user) {
      throw new Error('Invalid response from server');
    }

    setUser(response.user);
    setIsAuthenticated(true);
  } catch (err: any) {
    const errorMessage =
      err?.response?.data?.error ||
      err?.message ||
      'Social login failed';

    setError(errorMessage);
    throw new Error(errorMessage);
  } finally {
    setIsLoading(false);
  }
}, []);

  const logoutUser = useCallback(async () => {
    setIsLoading(true);
    try {
      await logout();
    } catch (e) {
      console.error('Logout error:', e);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
      setError(null);
    }
  }, []);

  const value = {
    user,
    isAuthenticated,
    isLoading,
    error,
    socialLogin,
    logoutUser,
    setError,
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};