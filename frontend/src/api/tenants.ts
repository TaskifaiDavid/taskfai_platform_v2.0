/**
 * Tenant Management API Service
 *
 * Admin API calls for tenant CRUD operations
 */

import { apiClient } from '@/lib/api'
import type {
  TenantCreate,
  TenantUpdate,
  Tenant,
  TenantListResponse,
  UserTenant,
} from '@/types/tenant'

/**
 * Create new tenant
 */
export async function createTenant(data: TenantCreate): Promise<Tenant> {
  return await apiClient.post<Tenant>('/admin/tenants', data)
}

/**
 * List all tenants with pagination
 */
export async function listTenants(params?: {
  limit?: number
  offset?: number
  active_only?: boolean
}): Promise<TenantListResponse> {
  return await apiClient.get<TenantListResponse>('/admin/tenants', params)
}

/**
 * Get tenant by ID
 */
export async function getTenant(tenantId: string): Promise<Tenant> {
  return await apiClient.get<Tenant>(`/admin/tenants/${tenantId}`)
}

/**
 * Update tenant
 */
export async function updateTenant(
  tenantId: string,
  data: TenantUpdate
): Promise<Tenant> {
  return await apiClient.patch<Tenant>(`/admin/tenants/${tenantId}`, data)
}

/**
 * Add user to tenant
 */
export async function addUserToTenant(
  tenantId: string,
  user: UserTenant
): Promise<{ message: string }> {
  return await apiClient.post<{ message: string }>(
    `/admin/tenants/${tenantId}/users`,
    user
  )
}

/**
 * Test Supabase connection
 */
export async function testSupabaseConnection(
  url: string,
  anonKey: string
): Promise<{ success: boolean; message: string }> {
  try {
    // Simple test: Try to create a Supabase client and ping it
    const response = await fetch(`${url}/rest/v1/`, {
      headers: {
        apikey: anonKey,
        Authorization: `Bearer ${anonKey}`,
      },
    })

    if (response.ok) {
      return { success: true, message: 'Connection successful' }
    } else {
      return {
        success: false,
        message: `Connection failed: ${response.status} ${response.statusText}`,
      }
    }
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Connection failed',
    }
  }
}
