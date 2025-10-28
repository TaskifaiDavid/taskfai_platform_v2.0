/**
 * Widget Registry
 *
 * Central registry of all available widgets with their metadata
 * and configuration schemas. Used by the dashboard builder.
 */

import { WidgetType } from '@/types/dashboardConfig'
import type { WidgetMetadata } from '@/types/widgetBuilder'

/**
 * Widget Registry - maps widget types to their metadata
 */
export const WIDGET_REGISTRY: Record<WidgetType, WidgetMetadata> = {
  [WidgetType.KPI_GRID]: {
    type: WidgetType.KPI_GRID,
    name: 'KPI Grid',
    description: 'Display multiple key performance indicators in a grid layout',
    icon: 'BarChart3',
    category: 'metrics',
    configSchema: {
      dataSource: {
        type: 'multiselect',
        options: [
          { value: 'total_revenue', label: 'Total Revenue', description: 'Total sales across all channels' },
          { value: 'total_units', label: 'Total Units Sold', description: 'Total number of units sold' },
          { value: 'avg_price', label: 'Average Price', description: 'Average price per unit' },
          { value: 'total_uploads', label: 'Total Uploads', description: 'Number of files uploaded' },
          { value: 'gross_profit', label: 'Gross Profit', description: 'Revenue minus costs and fees' },
          { value: 'profit_margin', label: 'Profit Margin', description: 'Profit as percentage of revenue' },
          { value: 'unique_countries', label: 'Countries', description: 'Number of countries with orders' },
          { value: 'order_count', label: 'Order Count', description: 'Total number of orders placed' },
          { value: 'reseller_count', label: 'Reseller Count', description: 'Number of active resellers' },
          { value: 'category_mix', label: 'Category Mix', description: 'Product category distribution' },
          { value: 'yoy_growth', label: 'YoY Growth', description: 'Year-over-year growth percentage' },
          { value: 'top_products', label: 'Top Products', description: 'Best-selling products' }
        ],
        required: true
      },
      displayOptions: {
        showTrend: {
          type: 'boolean',
          label: 'Show Trend Indicators',
          default: true,
          helpText: 'Display trend arrows and percentage changes'
        },
        showTotal: {
          type: 'boolean',
          label: 'Show Total Values',
          default: true
        }
      },
      filterOptions: {
        dateRange: {
          type: 'daterange',
          label: 'Date Range',
          presets: [
            { value: 'last_7_days', label: 'Last 7 Days' },
            { value: 'last_30_days', label: 'Last 30 Days' },
            { value: 'last_90_days', label: 'Last 90 Days' },
            { value: 'this_month', label: 'This Month' },
            { value: 'last_month', label: 'Last Month' },
            { value: 'this_year', label: 'This Year' },
            { value: 'custom', label: 'Custom Range' }
          ],
          default: 'last_30_days'
        }
      }
    }
  },

  [WidgetType.REVENUE_CHART]: {
    type: WidgetType.REVENUE_CHART,
    name: 'Revenue Chart',
    description: 'Visualize revenue trends over time',
    icon: 'TrendingUp',
    category: 'charts',
    configSchema: {
      displayOptions: {
        chartType: {
          type: 'select',
          label: 'Chart Type',
          options: [
            { value: 'line', label: 'Line Chart' },
            { value: 'bar', label: 'Bar Chart' },
            { value: 'area', label: 'Area Chart' }
          ],
          default: 'line',
          helpText: 'Choose how to visualize the revenue data'
        },
        groupBy: {
          type: 'select',
          label: 'Group By',
          options: [
            { value: 'day', label: 'Daily' },
            { value: 'week', label: 'Weekly' },
            { value: 'month', label: 'Monthly' },
            { value: 'quarter', label: 'Quarterly' }
          ],
          default: 'month'
        }
      },
      filterOptions: {
        dateRange: {
          type: 'daterange',
          label: 'Date Range',
          presets: [
            { value: 'last_30_days', label: 'Last 30 Days' },
            { value: 'last_90_days', label: 'Last 90 Days' },
            { value: 'last_6_months', label: 'Last 6 Months' },
            { value: 'this_year', label: 'This Year' },
            { value: 'last_year', label: 'Last Year' }
          ],
          default: 'last_90_days'
        }
      },
      visualOptions: {
        showLegend: {
          type: 'boolean',
          label: 'Show Legend',
          default: true
        },
        showLabels: {
          type: 'boolean',
          label: 'Show Data Labels',
          default: false
        }
      }
    }
  },

  [WidgetType.SALES_TREND]: {
    type: WidgetType.SALES_TREND,
    name: 'Sales Trend',
    description: 'Track sales performance over time with comparison',
    icon: 'LineChart',
    category: 'charts',
    configSchema: {
      displayOptions: {
        chartType: {
          type: 'select',
          label: 'Chart Type',
          options: [
            { value: 'line', label: 'Line Chart' },
            { value: 'area', label: 'Area Chart' }
          ],
          default: 'area'
        },
        groupBy: {
          type: 'select',
          label: 'Group By',
          options: [
            { value: 'day', label: 'Daily' },
            { value: 'week', label: 'Weekly' },
            { value: 'month', label: 'Monthly' }
          ],
          default: 'day'
        }
      },
      filterOptions: {
        dateRange: {
          type: 'daterange',
          label: 'Date Range',
          presets: [
            { value: 'last_7_days', label: 'Last 7 Days' },
            { value: 'last_30_days', label: 'Last 30 Days' },
            { value: 'last_90_days', label: 'Last 90 Days' }
          ],
          default: 'last_30_days'
        }
      }
    }
  },

  [WidgetType.TOP_PRODUCTS]: {
    type: WidgetType.TOP_PRODUCTS,
    name: 'Top Products',
    description: 'See your best-selling products ranked by revenue or quantity',
    icon: 'Package',
    category: 'tables',
    configSchema: {
      displayOptions: {
        sortBy: {
          type: 'select',
          label: 'Sort By',
          options: [
            { value: 'revenue', label: 'Revenue' },
            { value: 'quantity', label: 'Quantity Sold' },
            { value: 'orders', label: 'Number of Orders' }
          ],
          default: 'revenue',
          helpText: 'How to rank the products'
        },
        limit: {
          type: 'number',
          label: 'Number of Products',
          min: 5,
          max: 50,
          default: 10,
          helpText: 'How many products to display'
        }
      },
      filterOptions: {
        dateRange: {
          type: 'daterange',
          label: 'Date Range',
          presets: [
            { value: 'last_30_days', label: 'Last 30 Days' },
            { value: 'last_90_days', label: 'Last 90 Days' },
            { value: 'this_year', label: 'This Year' }
          ],
          default: 'last_30_days'
        },
        categories: {
          type: 'multiselect',
          label: 'Filter by Categories',
          options: [], // Will be populated dynamically from user data
          default: [],
          helpText: 'Optional: Filter to specific product categories'
        }
      }
    }
  },

  [WidgetType.RESELLER_PERFORMANCE]: {
    type: WidgetType.RESELLER_PERFORMANCE,
    name: 'Reseller Performance',
    description: 'Compare performance across different resellers',
    icon: 'Users',
    category: 'tables',
    configSchema: {
      displayOptions: {
        sortBy: {
          type: 'select',
          label: 'Sort By',
          options: [
            { value: 'revenue', label: 'Revenue' },
            { value: 'quantity', label: 'Quantity Sold' },
            { value: 'orders', label: 'Number of Orders' }
          ],
          default: 'revenue'
        },
        limit: {
          type: 'number',
          label: 'Number of Resellers',
          min: 5,
          max: 25,
          default: 10
        }
      },
      filterOptions: {
        dateRange: {
          type: 'daterange',
          label: 'Date Range',
          presets: [
            { value: 'last_30_days', label: 'Last 30 Days' },
            { value: 'last_90_days', label: 'Last 90 Days' },
            { value: 'this_year', label: 'This Year' }
          ],
          default: 'last_90_days'
        }
      }
    }
  },

  [WidgetType.CATEGORY_REVENUE]: {
    type: WidgetType.CATEGORY_REVENUE,
    name: 'Category Revenue',
    description: 'Revenue breakdown by product category',
    icon: 'PieChart',
    category: 'charts',
    configSchema: {
      displayOptions: {
        chartType: {
          type: 'select',
          label: 'Chart Type',
          options: [
            { value: 'pie', label: 'Pie Chart' },
            { value: 'donut', label: 'Donut Chart' },
            { value: 'bar', label: 'Bar Chart' }
          ],
          default: 'donut'
        }
      },
      filterOptions: {
        dateRange: {
          type: 'daterange',
          label: 'Date Range',
          presets: [
            { value: 'last_30_days', label: 'Last 30 Days' },
            { value: 'last_90_days', label: 'Last 90 Days' },
            { value: 'this_year', label: 'This Year' }
          ],
          default: 'last_30_days'
        }
      },
      visualOptions: {
        showLegend: {
          type: 'boolean',
          label: 'Show Legend',
          default: true
        },
        showLabels: {
          type: 'boolean',
          label: 'Show Percentage Labels',
          default: true
        }
      }
    }
  },

  [WidgetType.RECENT_UPLOADS]: {
    type: WidgetType.RECENT_UPLOADS,
    name: 'Recent Uploads',
    description: 'List of recently uploaded files with processing status',
    icon: 'FileUp',
    category: 'lists',
    configSchema: {
      displayOptions: {
        limit: {
          type: 'number',
          label: 'Number of Uploads',
          min: 5,
          max: 20,
          default: 5,
          helpText: 'How many recent uploads to display'
        }
      }
    }
  },

  [WidgetType.TOP_PRODUCTS_CHART]: {
    type: WidgetType.TOP_PRODUCTS_CHART,
    name: 'Top Products Chart',
    description: 'Horizontal bar chart showing top 10 products by revenue',
    icon: 'Package',
    category: 'charts',
    configSchema: {}
  },

  [WidgetType.TOP_RESELLERS_CHART]: {
    type: WidgetType.TOP_RESELLERS_CHART,
    name: 'Top Resellers Chart',
    description: 'Horizontal bar chart showing top 10 resellers by revenue',
    icon: 'Users',
    category: 'charts',
    configSchema: {}
  },

  [WidgetType.CHANNEL_MIX]: {
    type: WidgetType.CHANNEL_MIX,
    name: 'Channel Mix',
    description: 'Revenue and units breakdown by sales channel',
    icon: 'Laptop',
    category: 'metrics',
    configSchema: {}
  },

  [WidgetType.TOP_MARKETS]: {
    type: WidgetType.TOP_MARKETS,
    name: 'Top Markets',
    description: 'Top 7 countries by revenue',
    icon: 'Globe',
    category: 'metrics',
    configSchema: {}
  },

  [WidgetType.TOP_STORES]: {
    type: WidgetType.TOP_STORES,
    name: 'Top Stores',
    description: 'Top 10 stores by revenue with location details',
    icon: 'Store',
    category: 'metrics',
    configSchema: {}
  }
}

/**
 * Get widget metadata by type
 */
export function getWidgetMetadata(type: WidgetType): WidgetMetadata {
  return WIDGET_REGISTRY[type]
}

/**
 * Get all widget metadata grouped by category
 */
export function getWidgetsByCategory() {
  const byCategory: Record<string, WidgetMetadata[]> = {
    metrics: [],
    charts: [],
    tables: [],
    lists: []
  }

  Object.values(WIDGET_REGISTRY).forEach(widget => {
    byCategory[widget.category].push(widget)
  })

  return byCategory
}

/**
 * Get all available widgets as array
 */
export function getAllWidgets(): WidgetMetadata[] {
  return Object.values(WIDGET_REGISTRY)
}
