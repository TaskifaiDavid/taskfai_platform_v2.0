/**
 * Dynamic Dashboard Component
 *
 * Renders dashboard widgets dynamically based on database configuration.
 * Implements Option 1: Database-Driven Dashboards.
 */

import { WidgetType, type WidgetConfig, type DashboardConfig } from '@/types/dashboardConfig'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

// Widget Components
import { KPIGridWidget } from './widgets/KPIGridWidget'
import { RecentUploadsWidget } from './widgets/RecentUploadsWidget'
import { TopProductsWidget } from './widgets/TopProductsWidget'
import { ResellerPerformanceWidget } from './widgets/ResellerPerformanceWidget'
import { SalesTrendWidget } from './widgets/SalesTrendWidget'
import { RevenueChartWidget } from './widgets/RevenueChartWidget'
import { CategoryRevenueWidget } from './widgets/CategoryRevenueWidget'

interface DynamicDashboardProps {
  config: DashboardConfig
  className?: string
}

/**
 * Widget renderer - maps widget type to component
 */
function DynamicWidget({ widget }: { widget: WidgetConfig }) {
  switch (widget.type) {
    case WidgetType.KPI_GRID:
      return <KPIGridWidget config={widget} />

    case WidgetType.RECENT_UPLOADS:
      return <RecentUploadsWidget config={widget} />

    case WidgetType.TOP_PRODUCTS:
      return <TopProductsWidget config={widget} />

    case WidgetType.RESELLER_PERFORMANCE:
      return <ResellerPerformanceWidget config={widget} />

    case WidgetType.CATEGORY_REVENUE:
      return <CategoryRevenueWidget config={widget} />

    case WidgetType.REVENUE_CHART:
      return <RevenueChartWidget config={widget} />

    case WidgetType.SALES_TREND:
      return <SalesTrendWidget config={widget} />

    default:
      return (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Unknown widget type: {widget.type}
          </AlertDescription>
        </Alert>
      )
  }
}

export function DynamicDashboard({ config, className }: DynamicDashboardProps) {
  if (!config) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load dashboard configuration.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className={cn("space-y-6 animate-in fade-in-0 slide-in-from-bottom-4 duration-500", className)}>
      {config.layout.map((widget) => (
        <div key={widget.id} className="w-full">
          <DynamicWidget widget={widget} />
        </div>
      ))}
    </div>
  )
}
