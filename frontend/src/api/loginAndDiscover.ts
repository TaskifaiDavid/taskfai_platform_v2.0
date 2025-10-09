/**
 * Login and Discover API Client
 *
 * Combined authentication + tenant discovery for Flow B
 */

import { apiClient } from '@/lib/api'
import type { TenantOption } from './tenant'

// ============================================
// Request/Response Types
// ============================================

export interface LoginAndDiscoverRequest {
  email: string
  password: string
}

export interface LoginAndDiscoverSingleResponse {
  type: 'single'
  subdomain: string
  company_name: string
  redirect_url: string
  access_token: string
}

export interface LoginAndDiscoverMultiResponse {
  type: 'multi'
  tenants: TenantOption[]
  temp_token: string
}

export type LoginAndDiscoverResponse =
  | LoginAndDiscoverSingleResponse
  | LoginAndDiscoverMultiResponse

// ============================================
// Type Guards
// ============================================

export function isSingleTenantLogin(
  response: LoginAndDiscoverResponse
): response is LoginAndDiscoverSingleResponse {
  return response.type === 'single'
}

export function isMultiTenantLogin(
  response: LoginAndDiscoverResponse
): response is LoginAndDiscoverMultiResponse {
  return response.type === 'multi'
}

// ============================================
// API Functions
// ============================================

/**
 * Combined login + tenant discovery
 *
 * Authenticates user and discovers associated tenants in single request.
 *
 * Single tenant: Returns JWT token + redirect URL to dashboard
 * Multi tenant: Returns temp token + list of tenants for selection
 *
 * @param email - User email address
 * @param password - User password
 * @returns Login and discovery response
 * @throws Error if authentication fails
 */
export async function loginAndDiscover(
  email: string,
  password: string
): Promise<LoginAndDiscoverResponse> {
  try {
    const response = await apiClient.post<LoginAndDiscoverResponse>(
      '/api/auth/login-and-discover',
      { email, password }
    )
    return response
  } catch (error: any) {
    // Handle specific error cases
    if (error.response?.status === 401) {
      throw new Error('Invalid email or password')
    } else if (error.response?.status === 429) {
      throw new Error('Too many login attempts. Please try again later.')
    } else if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail)
    }
    throw new Error('Login failed. Please try again.')
  }
}

/**
 * Store access token in localStorage
 *
 * @param token - JWT access token
 */
export function storeAccessToken(token: string): void {
  localStorage.setItem('access_token', token)
}

/**
 * Store temporary token in sessionStorage (short-lived)
 *
 * @param tempToken - Temporary JWT token for tenant selection
 */
export function storeTempToken(tempToken: string): void {
  sessionStorage.setItem('temp_token', tempToken)
}

/**
 * Get temporary token from sessionStorage
 *
 * @returns Temporary token or null if not found
 */
export function getTempToken(): string | null {
  return sessionStorage.getItem('temp_token')
}

/**
 * Clear temporary token from sessionStorage
 */
export function clearTempToken(): void {
  sessionStorage.removeItem('temp_token')
}

/**
 * Build tenant dashboard URL from subdomain
 *
 * @param subdomain - Tenant subdomain
 * @returns Full dashboard URL
 */
export function buildDashboardUrl(subdomain: string): string {
  return `https://${subdomain}.taskifai.com/dashboard`
}
