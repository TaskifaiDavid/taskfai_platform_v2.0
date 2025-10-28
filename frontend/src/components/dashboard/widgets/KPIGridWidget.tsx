import { useDashboardData } from '@/api/analytics'
import { KPICard } from '@/components/analytics/KPICard'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Euro, Package, TrendingUp, ShoppingCart, Zap, Gauge } from 'lucide-react'
import type { WidgetConfig } from '@/types/dashboardConfig'

interface KPIGridWidgetProps {
  config: WidgetConfig
}

export function KPIGridWidget({ config }: KPIGridWidgetProps) {
  const { data: dashboard, isLoading } = useDashboardData()
  const kpiList = config.props.kpis as string[] || []
  const kpis = dashboard?.kpis

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Mock sparkline data (would come from API in production)
  const revenueSparkline = [42000, 45000, 43500, 47000, 49000, 48500, 52000, 54000, 53000, 56000, 58000, 60000]
  const unitsSparkline = [850, 920, 880, 950, 1020, 990, 1080, 1150, 1120, 1200, 1280, 1320]
  const priceSparkline = [48, 49, 47, 50, 48, 49, 48, 47, 47, 47, 45, 45]
  const ordersSparkline = [120, 145, 130, 160, 175, 165, 190, 210, 200, 225, 240, 260]

  if (isLoading) {
    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(kpiList.length)].map((_, i) => (
          <Card key={i} className="border-border bg-card shadow-sm animate-pulse">
            <CardContent className="pt-6">
              <Skeleton className="h-28 w-full bg-muted" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      {kpiList.includes('total_revenue') && (
        <KPICard
          title="Total Revenue"
          value={kpis ? formatCurrency(kpis.total_revenue) : '€0'}
          icon={Euro}
          trend={{ value: 12.5, isPositive: true }}
          sparklineData={revenueSparkline}
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}

      {kpiList.includes('total_units') && (
        <KPICard
          title="Total Units Sold"
          value={kpis?.total_units.toLocaleString() || '0'}
          icon={Package}
          trend={{ value: 8.2, isPositive: true }}
          sparklineData={unitsSparkline}
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}

      {kpiList.includes('average_order_value') && (
        <KPICard
          title="Average Order Value"
          value={kpis ? formatCurrency(kpis.average_order_value) : '€0'}
          icon={TrendingUp}
          trend={{ value: 3.1, isPositive: true }}
          sparklineData={priceSparkline}
          subtitle="Per transaction"
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}

      {kpiList.includes('units_per_transaction') && (
        <KPICard
          title="Units Per Transaction"
          value={kpis?.units_per_transaction.toFixed(1) || '0'}
          icon={Gauge}
          trend={{ value: 5.2, isPositive: true }}
          subtitle="Average units"
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}

      {kpiList.includes('fast_moving_products') && (
        <KPICard
          title="Fast Moving Products"
          value={kpis?.fast_moving_products.toLocaleString() || '0'}
          icon={Zap}
          subtitle="Sold in 30 days"
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}

      {kpiList.includes('slow_moving_products') && (
        <KPICard
          title="Slow Moving Products"
          value={kpis?.slow_moving_products.toLocaleString() || '0'}
          icon={Package}
          subtitle="Over 90 days"
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}

      {kpiList.includes('order_count') && (
        <KPICard
          title="Total Orders"
          value={kpis?.order_count?.toLocaleString() || '0'}
          icon={ShoppingCart}
          trend={{ value: 11.2, isPositive: true }}
          sparklineData={ordersSparkline}
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}
    </div>
  )
}
