export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  role?: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  initialize: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  socialLogin: (provider: 'google' | 'github', code: string) => Promise<void>;
  logout: () => Promise<void>;
  setError: (error: string | null) => void;
}
