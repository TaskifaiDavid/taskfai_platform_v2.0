// ABOUTME: Dashboard widget for displaying channel mix metrics (online, retail, B2B)
// ABOUTME: Wraps ChannelMixCard component with loading and error states
import { useDashboardData } from '@/api/analytics'
import { ChannelMixCard } from '@/components/analytics/ChannelMixCard'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import type { WidgetConfig } from '@/types/dashboardConfig'

interface ChannelMixWidgetProps {
  config: WidgetConfig
}

export function ChannelMixWidget({ config: _ }: ChannelMixWidgetProps) {
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
          Failed to load channel mix data.
        </AlertDescription>
      </Alert>
    )
  }

  if (!dashboard?.metrics?.channel_mix || dashboard.metrics.channel_mix.length === 0) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No channel data available.
        </AlertDescription>
      </Alert>
    )
  }

  return <ChannelMixCard data={dashboard.metrics.channel_mix} />
}
