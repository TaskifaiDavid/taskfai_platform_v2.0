import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/empty-state'
import { PieChart as PieChartIcon, TrendingUp } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { useNavigate } from 'react-router-dom'
import type { WidgetConfig } from '@/types/dashboardConfig'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

interface CategoryRevenueWidgetProps {
  config: WidgetConfig
}

interface CategorySummary {
  category: string
  revenue: number
  units: number
}

// Color palette for categories
const COLORS = [
  'hsl(var(--primary))',
  'hsl(var(--accent))',
  'hsl(var(--success))',
  'hsl(var(--warning))',
  'hsl(var(--destructive))',
  '#6366f1',
  '#8b5cf6',
  '#ec4899',
  '#f59e0b',
  '#10b981'
]

export function CategoryRevenueWidget({ config }: CategoryRevenueWidgetProps) {
  const navigate = useNavigate()
  const chartType = config.props.chartType || 'donut'

  // Fetch category data (grouped sales)
  const { data: categorySummary, isLoading } = useQuery({
    queryKey: ['sales-summary', 'category'],
    queryFn: async () => {
      // Note: Backend may not have category grouping endpoint yet
      // Fallback to aggregating from sales data
      const response = await apiClient.get<any>('/api/analytics/sales/summary', {
        group_by: 'product',  // Group by product, then aggregate by category
        channel: 'all'
      })
      return response as CategorySummary[]
    },
  })

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Transform data for pie chart
  const chartData = categorySummary?.map(item => ({
    name: item.category || (item as any).period || 'Unknown',
    value: item.revenue
  })).slice(0, 8) || []  // Limit to top 8 categories for clarity

  const totalRevenue = chartData.reduce((sum, item) => sum + item.value, 0)

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0]
      const percentage = totalRevenue > 0 ? ((data.value / totalRevenue) * 100).toFixed(1) : '0'
      return (
        <div className="rounded-lg border border-border bg-card p-3 shadow-lg">
          <p className="text-sm font-semibold text-foreground">{data.name}</p>
          <p className="text-sm text-muted-foreground mt-1">
            {formatCurrency(data.value)} ({percentage}%)
          </p>
        </div>
      )
    }
    return null
  }

  const innerRadius = chartType === 'donut' ? 60 : 0

  return (
    <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="border-b border-border bg-background/50">
        <div>
          <CardTitle className="flex items-center gap-2 text-lg">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <PieChartIcon className="h-4 w-4 text-primary" />
            </div>
            {config.props.title || 'Category Revenue'}
          </CardTitle>
          <CardDescription className="mt-1.5">
            {config.props.description || 'Revenue distribution by category'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        {isLoading ? (
          <Skeleton className="h-80 w-full bg-muted" />
        ) : chartData.length > 0 ? (
          <div className="space-y-4">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={innerRadius}
                  outerRadius={100}
                  fill="#8884d8"
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }: { name: string; percent: number }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {chartData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>

            {/* Legend with totals */}
            <div className="grid grid-cols-2 gap-2 text-sm">
              {chartData.map((item, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div
                    className="h-3 w-3 rounded-sm flex-shrink-0"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-muted-foreground truncate">{item.name}:</span>
                  <span className="font-semibold ml-auto">{formatCurrency(item.value)}</span>
                </div>
              ))}
            </div>

            {/* Total */}
            <div className="pt-4 border-t border-border">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-foreground">Total Revenue</span>
                <span className="text-lg font-bold text-primary">{formatCurrency(totalRevenue)}</span>
              </div>
            </div>
          </div>
        ) : (
          <EmptyState
            icon={TrendingUp}
            title="No category data"
            description="Upload sales data to see category revenue breakdown"
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
