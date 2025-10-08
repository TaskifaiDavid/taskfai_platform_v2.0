import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '@/types'
import { useAuthStore } from '@/stores/auth'

export function useLogin() {
  const setAuth = useAuthStore((state) => state.setAuth)

  return useMutation({
    mutationFn: (credentials: LoginRequest) =>
      apiClient.post<AuthResponse>('/api/auth/login', credentials),
    onSuccess: (data) => {
      setAuth(data.user, data.access_token)
    },
  })
}

export function useRegister() {
  const setAuth = useAuthStore((state) => state.setAuth)

  return useMutation({
    mutationFn: (data: RegisterRequest) =>
      apiClient.post<AuthResponse>('/api/auth/register', data),
    onSuccess: (data) => {
      setAuth(data.user, data.access_token)
    },
  })
}

export function useLogout() {
  const clearAuth = useAuthStore((state) => state.clearAuth)
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => apiClient.post('/api/auth/logout'),
    onSuccess: () => {
      clearAuth()
      queryClient.clear()
    },
  })
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: () => apiClient.get<User>('/api/auth/me'),
    retry: false,
  })
}
