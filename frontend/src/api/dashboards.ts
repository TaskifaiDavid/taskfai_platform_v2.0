import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import type { Dashboard, DashboardCreateRequest } from '@/types'

export function useDashboards() {
  return useQuery({
    queryKey: ['dashboards'],
    queryFn: () => apiClient.get<Dashboard[]>('/api/dashboards'),
  })
}

export function useCreateDashboard() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: DashboardCreateRequest) =>
      apiClient.post<Dashboard>('/api/dashboards', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] })
    },
  })
}

export function useUpdateDashboard() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<DashboardCreateRequest> }) =>
      apiClient.put<Dashboard>(`/api/dashboards/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] })
    },
  })
}

export function useDeleteDashboard() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/dashboards/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] })
    },
  })
}

export function useSetPrimaryDashboard() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiClient.patch<Dashboard>(`/api/dashboards/${id}/primary`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] })
    },
  })
}
