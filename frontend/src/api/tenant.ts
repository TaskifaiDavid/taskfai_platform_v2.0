/**
 * Tenant Discovery API Client
 *
 * Handles tenant discovery for multi-tenant login flow.
 */

import { apiClient } from '@/lib/api'

// Type Definitions

export interface TenantOption {
  subdomain: string
  company_name: string
}

export interface TenantDiscoverySingleResponse {
  subdomain: string
  company_name: string
  redirect_url: string
}

export interface TenantDiscoveryMultiResponse {
  tenants: TenantOption[]
}

export type TenantDiscoveryResponse = TenantDiscoverySingleResponse | TenantDiscoveryMultiResponse

// Type Guards

export function isSingleTenantResponse(
  response: TenantDiscoveryResponse
): response is TenantDiscoverySingleResponse {
  return 'redirect_url' in response
}

export function isMultiTenantResponse(
  response: TenantDiscoveryResponse
): response is TenantDiscoveryMultiResponse {
  return 'tenants' in response
}

// API Functions

/**
 * Discover tenant(s) for user email
 *
 * @param email - User email address
 * @returns Single tenant with redirect URL or list of tenants for selection
 * @throws Error if email not found in any tenant (404)
 */
export async function discoverTenant(email: string): Promise<TenantDiscoveryResponse> {
  const response = await apiClient.post<TenantDiscoveryResponse>(
    '/auth/discover-tenant',
    { email }
  )
  return response
}

/**
 * Build tenant login URL with pre-filled email
 *
 * @param subdomain - Tenant subdomain
 * @param email - User email to pre-fill
 * @returns Full login URL with email query parameter
 */
export function buildTenantLoginUrl(subdomain: string, email: string): string {
  const encodedEmail = encodeURIComponent(email)
  return `https://${subdomain}.taskifai.com/login?email=${encodedEmail}`
}

/**
 * Validate tenant redirect URL to prevent open redirect attacks
 *
 * @param url - URL to validate
 * @returns true if URL is safe taskifai.com subdomain
 */
export function isValidTenantUrl(url: string): boolean {
  try {
    const parsed = new URL(url)

    // Must be HTTPS
    if (parsed.protocol !== 'https:') {
      return false
    }

    // Must be taskifai.com subdomain
    const hostname = parsed.hostname
    const parts = hostname.split('.')

    // Must have at least 3 parts: subdomain.taskifai.com
    if (parts.length < 3) {
      return false
    }

    // Last two parts must be taskifai.com
    const domain = parts.slice(-2).join('.')
    if (domain !== 'taskifai.com') {
      return false
    }

    // Subdomain must be alphanumeric with hyphens only
    const subdomain = parts[0]
    const subdomainRegex = /^[a-z0-9-]+$/
    if (!subdomainRegex.test(subdomain)) {
      return false
    }

    return true
  } catch {
    return false
  }
}
