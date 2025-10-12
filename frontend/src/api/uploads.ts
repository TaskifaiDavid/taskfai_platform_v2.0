import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import type { Upload, UploadError } from '@/types'

// Backend response type with database field names
interface BackendUpload {
  upload_batch_id: string
  uploader_user_id: string
  original_filename: string
  file_size_bytes: number
  vendor_name?: string
  upload_mode: string
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  upload_timestamp: string
  processing_completed_at?: string
  total_rows_parsed?: number
  successful_inserts?: number
  failed_inserts?: number
}

// Transform backend response to frontend format
function transformUpload(backendUpload: BackendUpload): Upload {
  return {
    batch_id: backendUpload.upload_batch_id,
    filename: backendUpload.original_filename,
    status: backendUpload.processing_status,
    uploaded_at: backendUpload.upload_timestamp,
    processed_at: backendUpload.processing_completed_at,
    vendor_detected: backendUpload.vendor_name,
    total_rows: backendUpload.total_rows_parsed,
    successful_rows: backendUpload.successful_inserts,
    failed_rows: backendUpload.failed_inserts,
  }
}

export function useUploadFile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ file, mode = 'append' }: { file: File; mode?: 'append' | 'replace' }) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('mode', mode)
      return apiClient.getClient().post<Upload>('/api/uploads', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(res => res.data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['uploads'] })
    },
  })
}

export function useUploadsList() {
  return useQuery({
    queryKey: ['uploads'],
    queryFn: async () => {
      const response = await apiClient.get<{ success: boolean; batches: BackendUpload[]; count: number }>('/api/uploads/batches')
      return response.batches.map(transformUpload)
    },
    refetchInterval: 3000,  // Poll every 3 seconds to update upload statuses
    refetchIntervalInBackground: false,  // Stop polling when tab is inactive
  })
}

export function useUploadDetails(batchId: string | null) {
  return useQuery({
    queryKey: ['upload', batchId],
    queryFn: async () => {
      const response = await apiClient.get<{ success: boolean; batch: BackendUpload }>(`/api/uploads/batches/${batchId}`)
      return transformUpload(response.batch)
    },
    enabled: !!batchId,
    refetchInterval: 3000,  // Poll every 3 seconds to update batch details
    refetchIntervalInBackground: false,  // Stop polling when tab is inactive
  })
}

export function useUploadErrors(batchId: string | null) {
  return useQuery({
    queryKey: ['upload-errors', batchId],
    queryFn: () => apiClient.get<UploadError[]>(`/api/uploads/${batchId}/errors`),
    enabled: !!batchId,
  })
}
