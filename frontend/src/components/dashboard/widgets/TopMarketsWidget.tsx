// ABOUTME: Dashboard widget for displaying top 7 markets (countries) by revenue
// ABOUTME: Wraps TopMarketsCard component with loading and error states
import { useDashboardData } from '@/api/analytics'
import { TopMarketsCard } from '@/components/analytics/TopMarketsCard'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import type { WidgetConfig } from '@/types/dashboardConfig'

interface TopMarketsWidgetProps {
  config: WidgetConfig
}

export function TopMarketsWidget({ config: _ }: TopMarketsWidgetProps) {
  const { data: dashboard, isLoading, error } = useDashboardData()

  if (isLoading) {
    return (
      <Card className="border-border bg-card shadow-sm">
        <CardContent className="pt-6">
          <Skeleton className="h-[300px] w-full bg-muted" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load top markets data.
        </AlertDescription>
      </Alert>
    )
  }

  if (!dashboard?.metrics?.top_markets || dashboard.metrics.top_markets.length === 0) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No market data available.
        </AlertDescription>
      </Alert>
    )
  }

  return <TopMarketsCard data={dashboard.metrics.top_markets} />
}
