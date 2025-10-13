import { useSalesData } from '@/api/analytics'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { Users, ArrowUpRight } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { useNavigate } from 'react-router-dom'
import type { WidgetConfig } from '@/types/dashboardConfig'

interface ResellerPerformanceWidgetProps {
  config: WidgetConfig
}

interface ResellerData {
  reseller_name: string
  revenue: number
  units: number
  orders: number
}

export function ResellerPerformanceWidget({ config }: ResellerPerformanceWidgetProps) {
  const navigate = useNavigate()
  const { data: salesData, isLoading } = useSalesData({
    channel: 'offline',
    page: 1,
    page_size: config.props.limit || 10
  })

  const limit = config.props.limit || 10

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Aggregate sales data by reseller
  const resellerData: ResellerData[] = salesData?.sales?.reduce((acc: ResellerData[], sale: any) => {
    const existing = acc.find(r => r.reseller_name === sale.reseller_name)
    if (existing) {
      existing.revenue += sale.total_amount || 0
      existing.units += sale.quantity || 0
      existing.orders += 1
    } else {
      acc.push({
        reseller_name: sale.reseller_name || 'Unknown',
        revenue: sale.total_amount || 0,
        units: sale.quantity || 0,
        orders: 1
      })
    }
    return acc
  }, [])
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, limit) || []

  const totalRevenue = resellerData.reduce((sum, r) => sum + r.revenue, 0)

  return (
    <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="border-b border-border bg-background/50">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Users className="h-4 w-4 text-primary" />
              </div>
              {config.props.title || 'Reseller Performance'}
            </CardTitle>
            <CardDescription className="mt-1.5">
              {config.props.description || 'Top performing resellers by revenue'}
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/analytics')}
            className="hover:bg-primary/10 hover:text-primary"
          >
            View all
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="space-y-3">
          {isLoading ? (
            <>
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full bg-muted" />
              ))}
            </>
          ) : resellerData.length > 0 ? (
            resellerData.map((reseller, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between rounded-lg border border-border p-4 hover:bg-background/80 hover:border-primary/50 transition-all duration-200 group cursor-pointer"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex-shrink-0 border border-primary/30 font-bold text-primary">
                    <span className="text-sm">#{idx + 1}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold truncate group-hover:text-primary transition-colors">
                      {reseller.reseller_name}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {reseller.units.toLocaleString()} units • {reseller.orders} orders
                    </p>
                  </div>
                </div>
                <div className="text-right flex items-center gap-3">
                  <div>
                    <p className="text-sm font-bold text-foreground">{formatCurrency(reseller.revenue)}</p>
                    {totalRevenue > 0 && (
                      <div className="flex items-center gap-1 text-xs text-success mt-1">
                        <ArrowUpRight className="h-3 w-3" />
                        <span className="font-semibold">
                          {((reseller.revenue / totalRevenue) * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <EmptyState
              icon={Users}
              title="No reseller data yet"
              description="Upload sales data to see reseller performance"
              action={{
                label: "Upload Data",
                onClick: () => navigate('/uploads')
              }}
            />
          )}
        </div>
      </CardContent>
    </Card>
  )
}
