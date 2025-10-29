import axios, { type AxiosError, type AxiosInstance } from 'axios'
import type { APIError } from '@/types'

const REGISTRY_URL = 'https://taskifai-demo-ak4kq.ondigitalocean.app' // Backend discovery service
const LOCAL_API_URL = 'http://localhost:8000' // Fallback for local development

class APIClient {
  private client: AxiosInstance
  private backendUrl: string | null = null
  private discoveryInProgress: Promise<string> | null = null

  constructor() {
    // Initialize with local URL - will discover real backend URL on first request
    this.client = axios.create({
      baseURL: LOCAL_API_URL,
      withCredentials: true,
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

  private async discoverBackend(): Promise<string> {
    // Return cached URL if already discovered
    if (this.backendUrl) {
      return this.backendUrl as string
    }

    // Return in-progress discovery to avoid duplicate calls
    if (this.discoveryInProgress) {
      return this.discoveryInProgress as Promise<string>
    }

    // Start discovery process
    this.discoveryInProgress = (async () => {
      try {
        const hostname = window.location.hostname

        // Development mode - use localhost
        if (hostname === 'localhost' || /^\d+\.\d+\.\d+\.\d+$/.test(hostname)) {
          this.backendUrl = LOCAL_API_URL
          console.log('[API] Development mode - using localhost:', LOCAL_API_URL)
          return LOCAL_API_URL
        }

        // Extract subdomain (e.g., "bibbi" from "bibbi.taskifai.com")
        const parts = hostname.split('.')
        const subdomain = parts.length >= 3 ? parts[0] : 'demo'

        // Call discovery endpoint
        console.log('[API] Discovering backend for subdomain:', subdomain)
        const response = await fetch(
          `${REGISTRY_URL}/api/discover-backend?subdomain=${subdomain}`
        )

        if (!response.ok) {
          console.error('[API] Backend discovery failed, falling back to registry URL')
          this.backendUrl = REGISTRY_URL
          return REGISTRY_URL
        }

        const data = await response.json()
        this.backendUrl = data.backend_url

        // Update axios client baseURL
        this.client.defaults.baseURL = this.backendUrl as string

        console.log(`[API] Discovered backend for ${subdomain}:`, this.backendUrl)

        return this.backendUrl as string
      } catch (error) {
        console.error('[API] Backend discovery error:', error)
        // Fallback to registry URL
        this.backendUrl = REGISTRY_URL
        this.client.defaults.baseURL = REGISTRY_URL
        return REGISTRY_URL
      } finally {
        this.discoveryInProgress = null
      }
    })()

    return this.discoveryInProgress as Promise<string>
  }

  public getClient(): AxiosInstance {
    return this.client
  }

  // Helper methods - all call discoverBackend() before making requests
  public async get<T>(url: string, params?: unknown): Promise<T> {
    await this.discoverBackend()
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  public async post<T>(url: string, data?: unknown): Promise<T> {
    await this.discoverBackend()
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  public async put<T>(url: string, data?: unknown): Promise<T> {
    await this.discoverBackend()
    const response = await this.client.put<T>(url, data)
    return response.data
  }

  public async patch<T>(url: string, data?: unknown): Promise<T> {
    await this.discoverBackend()
    const response = await this.client.patch<T>(url, data)
    return response.data
  }

  public async delete<T>(url: string): Promise<T> {
    await this.discoverBackend()
    const response = await this.client.delete<T>(url)
    return response.data
  }
}

export const apiClient = new APIClient()
export default apiClient
