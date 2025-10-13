import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/empty-state'
import { BarChart3, TrendingUp } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { useNavigate } from 'react-router-dom'
import type { WidgetConfig } from '@/types/dashboardConfig'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface RevenueChartWidgetProps {
  config: WidgetConfig
}

interface SalesSummary {
  period: string
  revenue: number
  units: number
}

export function RevenueChartWidget({ config }: RevenueChartWidgetProps) {
  const navigate = useNavigate()
  const groupBy = config.props.groupBy || 'month'

  const { data: salesSummary, isLoading } = useQuery({
    queryKey: ['sales-summary', groupBy],
    queryFn: () => apiClient.get<SalesSummary[]>('/api/analytics/sales/summary', {
      group_by: groupBy,
      channel: 'all'
    }),
  })

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatPeriod = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      if (groupBy === 'month') {
        return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
      } else if (groupBy === 'product') {
        return dateStr
      }
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const chartData = salesSummary?.map(item => ({
    period: formatPeriod(item.period),
    revenue: item.revenue
  })) || []

  return (
    <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="border-b border-border bg-background/50">
        <div>
          <CardTitle className="flex items-center gap-2 text-lg">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <BarChart3 className="h-4 w-4 text-primary" />
            </div>
            {config.props.title || 'Revenue Chart'}
          </CardTitle>
          <CardDescription className="mt-1.5">
            {config.props.description || 'Revenue breakdown over time'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        {isLoading ? (
          <Skeleton className="h-80 w-full bg-muted" />
        ) : chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis
                dataKey="period"
                className="text-xs text-muted-foreground"
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis
                className="text-xs text-muted-foreground"
                tickFormatter={(value) => formatCurrency(value)}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  padding: '12px'
                }}
                formatter={(value: number) => [formatCurrency(value), 'Revenue']}
              />
              <Legend />
              <Bar
                dataKey="revenue"
                fill="hsl(var(--primary))"
                radius={[8, 8, 0, 0]}
                name="Revenue"
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState
            icon={TrendingUp}
            title="No revenue data"
            description="Upload sales data to visualize revenue trends"
            action={{
              label: "Upload Data",
              onClick: () => navigate('/uploads')
            }}
          />
        )}
      </CardContent>
    </Card>
  )
}
