import axios, { type AxiosError, type AxiosInstance } from 'axios'
import type { APIError } from '@/types'

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor: Add auth token and tenant headers
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Extract subdomain for tenant context
        const hostname = window.location.hostname
        const subdomain = this.extractSubdomain(hostname)
        if (subdomain) {
          config.headers['X-Tenant-Subdomain'] = subdomain
        }

        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor: Handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<APIError>) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  private extractSubdomain(hostname: string): string | null {
    // localhost or IP addresses don't have subdomains
    if (hostname === 'localhost' || /^\d+\.\d+\.\d+\.\d+$/.test(hostname)) {
      return 'demo' // Default to demo tenant for local development
    }

    const parts = hostname.split('.')
    if (parts.length >= 3) {
      return parts[0] // Return first part as subdomain
    }
    return null
  }

  public getClient(): AxiosInstance {
    return this.client
  }

  // Helper methods
  public async get<T>(url: string, params?: unknown): Promise<T> {
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  public async post<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  public async put<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.put<T>(url, data)
    return response.data
  }

  public async patch<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.patch<T>(url, data)
    return response.data
  }

  public async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url)
    return response.data
  }
}

export const apiClient = new APIClient()
export default apiClient
