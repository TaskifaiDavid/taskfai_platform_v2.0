/**
 * Widget Builder Types
 *
 * Defines the schema for visual widget configuration
 * Used by the dashboard builder UI
 */

import { WidgetType, type WidgetConfig } from './dashboardConfig'

/**
 * Widget Metadata - describes widget capabilities and configuration options
 */
export interface WidgetMetadata {
  type: WidgetType
  name: string
  description: string
  icon: string // Lucide icon name
  category: 'metrics' | 'charts' | 'tables' | 'lists'
  configSchema: WidgetConfigSchema
  previewImage?: string
}

/**
 * Widget Configuration Schema
 * Defines what options are available for each widget type
 */
export interface WidgetConfigSchema {
  // Data source configuration
  dataSource?: {
    type: 'select' | 'multiselect'
    options: DataSourceOption[]
    required: boolean
  }

  // Display options
  displayOptions?: {
    showTotal?: BooleanOption
    showTrend?: BooleanOption
    chartType?: SelectOption
    groupBy?: SelectOption
    sortBy?: SelectOption
    limit?: NumberOption
  }

  // Filter options
  filterOptions?: {
    dateRange?: DateRangeOption
    categories?: MultiSelectOption
    resellers?: MultiSelectOption
  }

  // Visual customization
  visualOptions?: {
    colorScheme?: SelectOption
    showLegend?: BooleanOption
    showLabels?: BooleanOption
  }
}

/**
 * Configuration Option Types
 */
export interface BooleanOption {
  type: 'boolean'
  label: string
  default: boolean
  helpText?: string
}

export interface SelectOption {
  type: 'select'
  label: string
  options: Array<{ value: string; label: string }>
  default?: string
  helpText?: string
}

export interface MultiSelectOption {
  type: 'multiselect'
  label: string
  options: Array<{ value: string; label: string }>
  default?: string[]
  helpText?: string
}

export interface NumberOption {
  type: 'number'
  label: string
  min?: number
  max?: number
  default?: number
  helpText?: string
}

export interface DateRangeOption {
  type: 'daterange'
  label: string
  presets: Array<{ value: string; label: string }>
  default?: string
  helpText?: string
}

export interface DataSourceOption {
  value: string
  label: string
  description?: string
}

/**
 * Widget Configuration Form State
 * Represents the current state while building/editing a widget
 */
export interface WidgetConfigFormState {
  widgetType: WidgetType
  title?: string

  // Data configuration
  dataSource?: string | string[]

  // Display settings
  showTotal?: boolean
  showTrend?: boolean
  chartType?: string
  groupBy?: string
  sortBy?: string
  limit?: number

  // Filters
  dateRange?: string
  categories?: string[]
  resellers?: string[]

  // Visual settings
  colorScheme?: string
  showLegend?: boolean
  showLabels?: boolean
}

/**
 * Widget Gallery Item
 * Represents a widget in the widget selection gallery
 */
export interface WidgetGalleryItem {
  metadata: WidgetMetadata
  isAvailable: boolean // Some widgets may require certain data
  tags: string[]
}

/**
 * Dashboard Builder State
 * Represents the overall state of the dashboard builder
 */
export interface DashboardBuilderState {
  dashboardName: string
  description?: string
  widgets: WidgetConfig[]
  isDefault: boolean
  displayOrder: number
}

/**
 * Dashboard Template
 * Pre-configured dashboard that users can clone
 */
export interface DashboardTemplate {
  id: string
  name: string
  description: string
  category: 'sales' | 'marketing' | 'operations' | 'executive'
  thumbnail?: string
  config: {
    layout: WidgetConfig[]
    kpis: string[]
  }
  tags: string[]
  isPopular?: boolean
}
