/**
 * Dashboard Configuration API
 * 
 * React Query hooks for dynamic dashboard configuration.
 * Implements Option 1: Database-Driven Dashboards.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import type {
  DashboardConfig,
  DashboardConfigListResponse,
  DashboardConfigCreate,
  DashboardConfigUpdate,
} from '@/types/dashboardConfig'

/**
 * Fetch default dashboard configuration for current user
 * Priority: user-specific default > tenant-wide default
 */
export function useDashboardConfig() {
  return useQuery({
    queryKey: ['dashboard-config', 'default'],
    queryFn: () => apiClient.get<DashboardConfig>('/api/dashboard-configs/default'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  })
}

/**
 * Fetch specific dashboard configuration by ID
 */
export function useDashboardConfigById(dashboardId: string | null) {
  return useQuery({
    queryKey: ['dashboard-config', dashboardId],
    queryFn: () => apiClient.get<DashboardConfig>(`/api/dashboard-configs/${dashboardId}`),
    enabled: !!dashboardId,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * List all dashboard configurations for current user
 */
export function useDashboardConfigList(includeTenantDefaults = true) {
  return useQuery({
    queryKey: ['dashboard-configs', includeTenantDefaults],
    queryFn: () => 
      apiClient.get<DashboardConfigListResponse>('/api/dashboard-configs', {
        include_tenant_defaults: includeTenantDefaults,
      }),
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Create new dashboard configuration
 */
export function useCreateDashboardConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (config: DashboardConfigCreate) =>
      apiClient.post<DashboardConfig>('/api/dashboard-configs', config),
    onSuccess: () => {
      // Invalidate dashboard config queries to refetch
      queryClient.invalidateQueries({ queryKey: ['dashboard-config'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-configs'] })
    },
  })
}

/**
 * Update existing dashboard configuration
 */
export function useUpdateDashboardConfig(dashboardId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (update: DashboardConfigUpdate) =>
      apiClient.put<DashboardConfig>(`/api/dashboard-configs/${dashboardId}`, update),
    onSuccess: () => {
      // Invalidate dashboard config queries to refetch
      queryClient.invalidateQueries({ queryKey: ['dashboard-config'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-configs'] })
    },
  })
}

/**
 * Delete dashboard configuration
 */
export function useDeleteDashboardConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (dashboardId: string) =>
      apiClient.delete(`/api/dashboard-configs/${dashboardId}`),
    onSuccess: () => {
      // Invalidate dashboard config queries to refetch
      queryClient.invalidateQueries({ queryKey: ['dashboard-config'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-configs'] })
    },
  })
}
