// ABOUTME: Dashboard widget for displaying top 10 resellers by revenue bar chart
// ABOUTME: Wraps TopResellersChart component with loading and error states
import { useDashboardData } from '@/api/analytics'
import { TopResellersChart } from '@/components/analytics/TopResellersChart'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import type { WidgetConfig } from '@/types/dashboardConfig'

interface TopResellersChartWidgetProps {
  config: WidgetConfig
}

export function TopResellersChartWidget({ config: _ }: TopResellersChartWidgetProps) {
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
          Failed to load top resellers data.
        </AlertDescription>
      </Alert>
    )
  }

  if (!dashboard?.charts?.top_resellers || dashboard.charts.top_resellers.length === 0) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No reseller data available.
        </AlertDescription>
      </Alert>
    )
  }

  return <TopResellersChart data={dashboard.charts.top_resellers} />
}
