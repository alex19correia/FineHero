'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';

export function useAuth() {
  const queryClient = useQueryClient();
  const router = useRouter();

  const { data: user, isLoading } = useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      try {
        const response = await api.get('/api/v1/users/profile');
        return response.data;
      } catch (error) {
        return null;
      }
    },
    staleTime: Infinity,
  });

  const loginMutation = useMutation({
    mutationFn: (credentials: any) => api.post('/api/v1/auth/login', credentials),
    onSuccess: (data) => {
      localStorage.setItem('finehero_token', data.data.token);
      queryClient.setQueryData(['user'], data.data.user);
      router.push('/dashboard');
    },
  });

  const registerMutation = useMutation({
    mutationFn: (userInfo: any) => api.post('/api/v1/auth/register', userInfo),
    onSuccess: (data) => {
      localStorage.setItem('finehero_token', data.data.token);
      queryClient.setQueryData(['user'], data.data.user);
      router.push('/dashboard');
    },
  });

  const logout = () => {
    localStorage.removeItem('finehero_token');
    queryClient.setQueryData(['user'], null);
    router.push('/login');
  };

  return {
    user,
    isLoading,
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout,
  };
}
