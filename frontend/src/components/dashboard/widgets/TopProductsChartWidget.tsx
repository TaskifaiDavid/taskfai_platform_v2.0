// ABOUTME: Dashboard widget for displaying top 10 products by revenue bar chart
// ABOUTME: Wraps TopProductsChart component with loading and error states
import { useDashboardData } from '@/api/analytics'
import { TopProductsChart } from '@/components/analytics/TopProductsChart'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import type { WidgetConfig } from '@/types/dashboardConfig'

interface TopProductsChartWidgetProps {
  config: WidgetConfig
}

export function TopProductsChartWidget({ config: _ }: TopProductsChartWidgetProps) {
  const { data: dashboard, isLoading, error } = useDashboardData()

  if (isLoading) {
    return (
      <Card className="border-border bg-card shadow-sm">
        <CardContent className="pt-6">
          <Skeleton className="h-[400px] w-full bg-muted" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load top products data.
        </AlertDescription>
      </Alert>
    )
  }

  if (!dashboard?.charts?.top_products || dashboard.charts.top_products.length === 0) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No product data available.
        </AlertDescription>
      </Alert>
    )
  }

  return <TopProductsChart data={dashboard.charts.top_products} />
}
