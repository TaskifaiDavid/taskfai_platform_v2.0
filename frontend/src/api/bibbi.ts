import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/lib/api'

// ============================================
// TYPES
// ============================================

export interface BibbιUpload {
  upload_id: string
  upload_batch_id: string
  reseller_id: string
  filename: string
  file_size: number
  file_hash: string
  upload_status: 'pending' | 'processing' | 'validated' | 'completed' | 'failed' | 'partial'
  vendor_name?: string
  total_rows?: number
  processed_rows?: number
  failed_rows?: number
  duplicated_rows?: number
  upload_timestamp: string
  processing_started_at?: string
  processing_completed_at?: string
  processing_errors?: {
    error_message?: string
    validation_errors?: any
    insertion_errors?: any
  }
}

export interface BibbιReseller {
  reseller_id: string
  reseller_name: string
  country?: string
  currency?: string
  is_active: boolean
  created_at: string
}

export interface BibbιProductMapping {
  mapping_id: string
  reseller_id: string
  product_code: string
  ean: string
  metadata?: {
    product_name?: string
    category?: string
  }
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface BibbιStore {
  store_id: string
  reseller_id: string
  store_identifier: string
  store_name: string
  store_type: 'physical' | 'online'
  country?: string
  city?: string
  is_active: boolean
  created_at: string
}

// ============================================
// UPLOAD API HOOKS
// ============================================

export function useBibbiUploadFile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ file, reseller_id }: { file: File; reseller_id: string }) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('reseller_id', reseller_id)

      return apiClient.getClient().post<BibbιUpload>('/api/bibbi/uploads', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(res => res.data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bibbi-uploads'] })
    },
  })
}

export function useBibbiUploadsList(statusFilter?: string) {
  return useQuery({
    queryKey: ['bibbi-uploads', statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (statusFilter) {
        params.append('status_filter', statusFilter)
      }

      const response = await apiClient.get<{ uploads: BibbιUpload[]; count: number }>(
        `/api/bibbi/uploads?${params.toString()}`
      )
      return response
    },
    refetchInterval: 5000,  // Poll every 5 seconds
    refetchIntervalInBackground: false,
  })
}

export function useBibbiUploadDetails(uploadId: string | null) {
  return useQuery({
    queryKey: ['bibbi-upload', uploadId],
    queryFn: async () => {
      return apiClient.get<BibbιUpload>(`/api/bibbi/uploads/${uploadId}`)
    },
    enabled: !!uploadId,
    refetchInterval: 5000,
    refetchIntervalInBackground: false,
  })
}

export function useBibbiRetryUpload() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (uploadId: string) => {
      return apiClient.post<{ message: string; upload_id: string; status: string }>(
        `/api/bibbi/uploads/${uploadId}/retry`
      )
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bibbi-uploads'] })
    },
  })
}

// ============================================
// RESELLER API HOOKS
// ============================================

export function useBibbiResellers() {
  return useQuery({
    queryKey: ['bibbi-resellers'],
    queryFn: async () => {
      // This endpoint doesn't exist yet, but we'll mock it for now
      // TODO: Create backend endpoint /api/bibbi/resellers
      return apiClient.get<BibbιReseller[]>('/api/bibbi/resellers')
    },
  })
}

// ============================================
// PRODUCT MAPPING API HOOKS
// ============================================

export function useBibbiProductMappings(resellerId: string | null) {
  return useQuery({
    queryKey: ['bibbi-product-mappings', resellerId],
    queryFn: async () => {
      return apiClient.get<{ mappings: BibbιProductMapping[]; total_count: number }>(
        `/api/bibbi/product-mappings?reseller_id=${resellerId}`
      )
    },
    enabled: !!resellerId,
  })
}

export function useBibbiCreateMapping() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      reseller_id: string
      product_code: string
      ean: string
      metadata?: { product_name?: string; category?: string }
    }) => {
      return apiClient.post<BibbιProductMapping>('/api/bibbi/product-mappings', data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bibbi-product-mappings'] })
    },
  })
}

export function useBibbiBulkCreateMappings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      reseller_id: string
      mappings: Array<{
        product_code: string
        ean: string
        metadata?: { product_name?: string; category?: string }
      }>
    }) => {
      return apiClient.post<{
        success: boolean
        success_count: number
        total_count: number
        created_mapping_ids: string[]
      }>('/api/bibbi/product-mappings/bulk', data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bibbi-product-mappings'] })
    },
  })
}

export function useBibbiDeleteMapping() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (mappingId: string) => {
      return apiClient.delete(`/api/bibbi/product-mappings/${mappingId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bibbi-product-mappings'] })
    },
  })
}

// ============================================
// STORE API HOOKS
// ============================================

export function useBibbiStores(resellerId: string | null) {
  return useQuery({
    queryKey: ['bibbi-stores', resellerId],
    queryFn: async () => {
      // This endpoint doesn't exist yet, but we'll mock it
      // TODO: Create backend endpoint /api/bibbi/stores
      return apiClient.get<BibbιStore[]>(
        `/api/bibbi/stores?reseller_id=${resellerId}`
      )
    },
    enabled: !!resellerId,
  })
}
