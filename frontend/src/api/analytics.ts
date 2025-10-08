import { useMutation, useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import type { KPIs, SalesFilter, SalesResponse, ExportRequest, ExportResponse } from '@/types'

export function useKPIs(dateFrom?: string, dateTo?: string) {
  return useQuery({
    queryKey: ['kpis', dateFrom, dateTo],
    queryFn: () => apiClient.get<KPIs>('/api/analytics/kpis', { date_from: dateFrom, date_to: dateTo }),
  })
}

export function useSalesData(filters: SalesFilter) {
  return useQuery({
    queryKey: ['sales', filters],
    queryFn: () => apiClient.get<SalesResponse>('/api/analytics/sales', filters),
  })
}

export function useExportReport() {
  return useMutation({
    mutationFn: (request: ExportRequest) =>
      apiClient.post<ExportResponse>('/api/analytics/export', request),
  })
}

export function useDownloadReport(taskId: string | null) {
  return useQuery({
    queryKey: ['export-status', taskId],
    queryFn: () => apiClient.get<ExportResponse>(`/api/analytics/download/${taskId}`),
    enabled: !!taskId,
    refetchInterval: (query) => {
      // Stop polling when completed or failed
      if (query.state.data && (query.state.data.status === 'completed' || query.state.data.status === 'failed')) {
        return false
      }
      return 2000 // Poll every 2 seconds
    },
  })
}
