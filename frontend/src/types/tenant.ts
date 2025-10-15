/**
 * Tenant Management Types
 *
 * Type definitions for multi-tenant administration
 */

export interface TenantCredentials {
  anon_key: string
  service_key: string
}

export interface TenantCreate {
  subdomain: string
  company_name: string
  database_url: string
  database_credentials: TenantCredentials
  admin_email: string
  admin_name?: string
  metadata?: Record<string, unknown>
}

export interface TenantUpdate {
  company_name?: string
  database_url?: string
  database_credentials?: TenantCredentials
  is_active?: boolean
  metadata?: Record<string, unknown>
}

export interface Tenant {
  tenant_id: string
  subdomain: string
  company_name: string
  database_url: string
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export interface TenantListResponse {
  tenants: Tenant[]
  total: number
  limit: number
  offset: number
}

export interface UserTenant {
  email: string
  role: 'member' | 'admin' | 'super_admin'
}

export interface TenantFormData {
  subdomain: string
  company_name: string
  database_url: string
  anon_key: string
  service_key: string
  admin_email: string
  admin_name: string
}
