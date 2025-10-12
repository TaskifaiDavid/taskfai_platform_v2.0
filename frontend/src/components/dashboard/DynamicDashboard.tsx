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
    case WidgetType.CATEGORY_REVENUE:
    case WidgetType.REVENUE_CHART:
    case WidgetType.SALES_TREND:
      return (
        <div className="rounded-lg border border-dashed border-border p-6 text-center">
          <p className="text-sm text-muted-foreground">
            Widget type <code className="px-2 py-1 bg-muted rounded">{widget.type}</code> coming soon
          </p>
        </div>
      )

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
    <div className={cn("space-y-8 animate-in fade-in-0 slide-in-from-bottom-4 duration-500", className)}>
      <div className="space-y-2">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-4xl font-bold tracking-tight">{config.dashboard_name}</h1>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-success/10 border border-success/30">
            <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
            <span className="text-xs font-semibold text-success">Live</span>
          </div>
        </div>
        {config.description && (
          <p className="text-base text-muted-foreground">{config.description}</p>
        )}
      </div>

      <div className="space-y-6">
        {config.layout.map((widget) => (
          <div key={widget.id} className="w-full">
            <DynamicWidget widget={widget} />
          </div>
        ))}
      </div>
    </div>
  )
}
