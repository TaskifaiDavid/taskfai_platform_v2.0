import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  LoginAndDiscoverResponse,
  ExchangeTokenRequest,
  ExchangeTokenResponse,
} from '@/types'
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

/**
 * Combined authentication + tenant discovery hook
 *
 * Used on central login portal (app.taskifai.com) for Flow B:
 * - Single tenant: Returns token + redirect URL directly
 * - Multi tenant: Returns temp token + tenant list for selection
 */
export function useLoginAndDiscover() {
  return useMutation({
    mutationFn: (credentials: LoginRequest) =>
      apiClient.post<LoginAndDiscoverResponse>('/api/auth/login-and-discover', credentials),
  })
}

/**
 * Exchange temporary token for tenant-scoped token
 *
 * Used when multi-tenant user selects a specific tenant.
 * Exchanges the temp token for a real JWT with tenant claims.
 */
export function useExchangeToken() {
  return useMutation({
    mutationFn: (request: ExchangeTokenRequest) =>
      apiClient.post<ExchangeTokenResponse>('/api/auth/exchange-token', request),
  })
}
