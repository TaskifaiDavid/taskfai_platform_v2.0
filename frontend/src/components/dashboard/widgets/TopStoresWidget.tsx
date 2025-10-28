// ABOUTME: Dashboard widget for displaying top 10 stores by revenue
// ABOUTME: Wraps TopStoresCard component with loading and error states
import { useDashboardData } from '@/api/analytics'
import { TopStoresCard } from '@/components/analytics/TopStoresCard'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import type { WidgetConfig } from '@/types/dashboardConfig'

interface TopStoresWidgetProps {
  config: WidgetConfig
}

export function TopStoresWidget({ config: _ }: TopStoresWidgetProps) {
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
          Failed to load top stores data.
        </AlertDescription>
      </Alert>
    )
  }

  if (!dashboard?.metrics?.top_stores || dashboard.metrics.top_stores.length === 0) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No store data available.
        </AlertDescription>
      </Alert>
    )
  }

  return <TopStoresCard data={dashboard.metrics.top_stores} />
}
