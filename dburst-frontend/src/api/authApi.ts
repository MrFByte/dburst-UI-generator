import api from './axiosConfig';

export const authApi = {
  login: (credentials: { email: string; password: string }) => 
    api.post('/auth/login', credentials),

  socialLogin: (provider: string, code: string) =>
    api.post(`/auth/${provider}`, { code }),

  logout: () => api.post('/auth/logout'),

  refreshToken: () => 
    api.post('/auth/refresh', {}, { 
      skipAuthRefresh: true
    }),

  getProfile: () => api.get('/auth/me')
};
