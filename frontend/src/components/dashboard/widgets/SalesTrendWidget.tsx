import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/empty-state'
import { LineChart, TrendingUp } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { useNavigate } from 'react-router-dom'
import type { WidgetConfig } from '@/types/dashboardConfig'
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface SalesTrendWidgetProps {
  config: WidgetConfig
}

interface SalesSummary {
  period: string
  revenue: number
  units: number
}

export function SalesTrendWidget({ config }: SalesTrendWidgetProps) {
  const navigate = useNavigate()

  const { data: salesSummary, isLoading } = useQuery({
    queryKey: ['sales-summary', 'month'],
    queryFn: () => apiClient.get<SalesSummary[]>('/api/analytics/sales/summary', {
      group_by: 'month',
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

  const formatMonth = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
    } catch {
      return dateStr
    }
  }

  const chartData = salesSummary?.map(item => ({
    month: formatMonth(item.period),
    revenue: item.revenue,
    units: item.units
  })) || []

  return (
    <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="border-b border-border bg-background/50">
        <div>
          <CardTitle className="flex items-center gap-2 text-lg">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <TrendingUp className="h-4 w-4 text-primary" />
            </div>
            {config.props.title || 'Sales Trend'}
          </CardTitle>
          <CardDescription className="mt-1.5">
            {config.props.description || 'Revenue and units sold over time'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        {isLoading ? (
          <Skeleton className="h-80 w-full bg-muted" />
        ) : chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <RechartsLineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis
                dataKey="month"
                className="text-xs text-muted-foreground"
              />
              <YAxis
                yAxisId="left"
                className="text-xs text-muted-foreground"
                tickFormatter={(value) => formatCurrency(value)}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                className="text-xs text-muted-foreground"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  padding: '12px'
                }}
                formatter={(value: number, name: string) => {
                  if (name === 'revenue') {
                    return [formatCurrency(value), 'Revenue']
                  }
                  return [value.toLocaleString(), 'Units']
                }}
              />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="revenue"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={{ fill: 'hsl(var(--primary))', r: 4 }}
                activeDot={{ r: 6 }}
                name="Revenue"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="units"
                stroke="hsl(var(--accent))"
                strokeWidth={2}
                dot={{ fill: 'hsl(var(--accent))', r: 4 }}
                activeDot={{ r: 6 }}
                name="Units"
              />
            </RechartsLineChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState
            icon={LineChart}
            title="No sales trend data"
            description="Upload sales data to visualize trends over time"
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
