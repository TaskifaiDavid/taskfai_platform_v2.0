/**
 * Dashboard Configuration Types
 * 
 * TypeScript types for dynamic dashboard configuration.
 * Matches backend Pydantic models.
 */

export enum KPIType {
  TOTAL_REVENUE = 'total_revenue',
  TOTAL_UNITS = 'total_units',
  AVG_PRICE = 'avg_price',
  TOTAL_UPLOADS = 'total_uploads',
  GROSS_PROFIT = 'gross_profit',
  PROFIT_MARGIN = 'profit_margin',
  UNIQUE_COUNTRIES = 'unique_countries',
  ORDER_COUNT = 'order_count',
  RESELLER_COUNT = 'reseller_count',
  CATEGORY_MIX = 'category_mix',
  YOY_GROWTH = 'yoy_growth',
  TOP_PRODUCTS = 'top_products',
}

export enum WidgetType {
  KPI_GRID = 'kpi_grid',
  RECENT_UPLOADS = 'recent_uploads',
  TOP_PRODUCTS = 'top_products',
  RESELLER_PERFORMANCE = 'reseller_performance',
  CATEGORY_REVENUE = 'category_revenue',
  REVENUE_CHART = 'revenue_chart',
  SALES_TREND = 'sales_trend',
}

export interface WidgetPosition {
  row: number
  col: number
  width: number
  height: number
}

export interface WidgetConfig {
  id: string
  type: WidgetType
  position: WidgetPosition
  props: Record<string, any>
}

export interface DashboardFilters {
  date_range: string
  vendor: string
  category?: string
  reseller?: string
}

export interface DashboardConfig {
  dashboard_id: string
  user_id: string | null
  dashboard_name: string
  description: string | null
  layout: WidgetConfig[]
  kpis: KPIType[]
  filters: DashboardFilters
  is_default: boolean
  is_active: boolean
  display_order: number
  created_at: string
  updated_at: string
}

export interface DashboardConfigSummary {
  dashboard_id: string
  dashboard_name: string
  description: string | null
  is_default: boolean
  is_active: boolean
  display_order: number
  widget_count: number
  kpi_count: number
  updated_at: string
}

export interface DashboardConfigListResponse {
  dashboards: DashboardConfigSummary[]
  total: number
  has_default: boolean
}

export interface DashboardConfigCreate {
  dashboard_name: string
  description?: string
  layout: WidgetConfig[]
  kpis: KPIType[]
  filters?: DashboardFilters
  is_default?: boolean
  is_active?: boolean
  display_order?: number
}

export interface DashboardConfigUpdate {
  dashboard_name?: string
  description?: string
  layout?: WidgetConfig[]
  kpis?: KPIType[]
  filters?: DashboardFilters
  is_default?: boolean
  is_active?: boolean
  display_order?: number
}
