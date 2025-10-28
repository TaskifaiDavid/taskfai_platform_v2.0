// User & Auth Types
export interface User {
  user_id: string
  email: string
  role: 'admin' | 'user'
  tenant_id: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  tenant_id: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

// Tenant Discovery Types
export interface TenantOption {
  subdomain: string
  company_name: string
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

export interface ExchangeTokenRequest {
  temp_token: string
  selected_subdomain: string
}

export interface ExchangeTokenResponse {
  access_token: string
  redirect_url: string
  subdomain: string
  company_name: string
}

// Upload Types
export interface Upload {
  batch_id: string
  filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  uploaded_at: string
  processed_at?: string
  vendor_detected?: string
  total_rows?: number
  successful_rows?: number
  failed_rows?: number
}

export interface UploadError {
  row_number: number
  error_message: string
  raw_data?: Record<string, unknown>
}

// Chat Types
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
  sql_generated?: string
}

export interface ChatQueryRequest {
  query: string
  session_id?: string
}

export interface ChatQueryResponse {
  response: string
  sql_generated?: string
  session_id: string
}

export interface Conversation {
  conversation_id: string
  session_id: string
  messages: ChatMessage[]
  created_at: string
}

// Dashboard Types
export interface Dashboard {
  config_id: string
  dashboard_name: string
  dashboard_type: 'tableau' | 'powerbi' | 'looker' | 'metabase' | 'other'
  dashboard_url: string
  is_primary: boolean
  created_at: string
  updated_at?: string
}

export interface DashboardCreateRequest {
  dashboard_name: string
  dashboard_type: Dashboard['dashboard_type']
  dashboard_url: string
  auth_token?: string
  is_primary?: boolean
}

// Analytics Types
export interface KPIs {
  total_revenue: number
  total_units: number
  avg_price: number
  total_uploads?: number
  gross_profit?: number
  profit_margin?: number
  unique_countries?: number
  order_count?: number
  top_products: Array<{
    product_name: string
    revenue: number
    units: number
  }>
  top_resellers: Array<{
    reseller_name: string
    revenue: number
  }>
}

// Comprehensive Dashboard Data
export interface DashboardData {
  kpis: {
    total_revenue: number
    total_units: number
    average_order_value: number
    units_per_transaction: number
    order_count: number
    fast_moving_products: number
    slow_moving_products: number
  }
  charts: {
    top_products: Array<{
      product_name: string
      product_ean: string
      revenue: number
      units: number
      transactions: number
      channel: string
    }>
    top_resellers: Array<{
      reseller_id: string
      reseller_name: string
      revenue: number
      units: number
      transactions: number
      store_count: number
    }>
  }
  metrics: {
    top_markets: Array<{
      country: string
      revenue: number
      units: number
      transactions: number
    }>
    top_stores: Array<{
      store_id: string
      store_name: string
      city: string
      country: string
      revenue: number
      units: number
      transactions: number
    }>
    channel_mix: Array<{
      channel: string
      revenue: number
      revenue_percentage: number
      units: number
      units_percentage: number
      transactions: number
    }>
    product_velocity: {
      fast_moving_count: number
      slow_moving_count: number
      fast_moving_products: Array<{
        product_ean: string
        product_name: string
        units_sold: number
        revenue: number
      }>
      days_thresholds: {
        fast_days: number
        slow_days: number
      }
    }
  }
  date_range: {
    start: string | null
    end: string | null
  }
  channel_filter: string | null
}

export interface SalesFilter {
  date_from?: string
  date_to?: string
  reseller_id?: string
  product_id?: string
  channel?: 'online' | 'offline'
  page?: number
  page_size?: number
}

export interface Sale {
  sale_id: string
  date: string
  reseller_name: string
  product_name: string
  units_sold: number
  revenue_eur: number
  channel: 'online' | 'offline'
}

export interface SalesResponse {
  sales: Sale[]
  total: number
  page: number
  page_size: number
}

export interface ExportRequest {
  format: 'pdf' | 'csv' | 'excel'
  date_from: string
  date_to: string
  filters?: Omit<SalesFilter, 'date_from' | 'date_to' | 'page' | 'page_size'>
}

export interface ExportResponse {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  download_url?: string
}

// Tenant Types (Admin)
export interface Tenant {
  tenant_id: string
  subdomain: string
  company_name: string
  is_active: boolean
  created_at: string
  last_activity?: string
}

export interface TenantCreateRequest {
  subdomain: string
  company_name: string
  admin_email: string
  admin_password: string
}

// Pagination
export interface PaginationParams {
  page?: number
  page_size?: number
}

// API Error
export interface APIError {
  detail: string
  status_code?: number
}

// Dashboard Configuration Types (Dynamic Dashboards)
export * from './dashboardConfig'
