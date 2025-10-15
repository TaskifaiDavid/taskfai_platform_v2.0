import { useKPIs } from '@/api/analytics'
import { KPICard } from '@/components/analytics/KPICard'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Euro, Package, TrendingUp, Upload as UploadIcon, DollarSign, Percent, Globe, ShoppingCart } from 'lucide-react'
import type { WidgetConfig } from '@/types/dashboardConfig'

interface KPIGridWidgetProps {
  config: WidgetConfig
}

export function KPIGridWidget({ config }: KPIGridWidgetProps) {
  const { data: kpis, isLoading } = useKPIs()
  const kpiList = config.props.kpis as string[] || []

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
  const uploadsSparkline = [2, 3, 2, 4, 3, 5, 4, 6, 5, 7, 6, 8]
  const profitSparkline = [15000, 18000, 17000, 20000, 22000, 21000, 24000, 26000, 25000, 28000, 30000, 32000]
  const marginSparkline = [35, 38, 36, 39, 42, 40, 43, 45, 44, 46, 48, 50]
  const countriesSparkline = [5, 6, 6, 7, 8, 8, 9, 10, 10, 11, 12, 13]
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

      {kpiList.includes('avg_price') && (
        <KPICard
          title="Average Price"
          value={kpis ? formatCurrency(kpis.avg_price) : '€0'}
          icon={TrendingUp}
          trend={{ value: 3.1, isPositive: false }}
          sparklineData={priceSparkline}
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}

      {kpiList.includes('total_uploads') && (
        <KPICard
          title="Total Uploads"
          value={kpis?.total_uploads?.toString() || '0'}
          icon={UploadIcon}
          sparklineData={uploadsSparkline}
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}

      {kpiList.includes('gross_profit') && (
        <KPICard
          title="Gross Profit"
          value={kpis ? formatCurrency(kpis.gross_profit || 0) : '€0'}
          icon={DollarSign}
          trend={{ value: 15.3, isPositive: true }}
          sparklineData={profitSparkline}
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}

      {kpiList.includes('profit_margin') && (
        <KPICard
          title="Profit Margin"
          value={kpis ? `${(kpis.profit_margin || 0).toFixed(1)}%` : '0%'}
          icon={Percent}
          trend={{ value: 2.8, isPositive: true }}
          sparklineData={marginSparkline}
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}

      {kpiList.includes('unique_countries') && (
        <KPICard
          title="Countries"
          value={kpis?.unique_countries?.toString() || '0'}
          icon={Globe}
          trend={{ value: 4.5, isPositive: true }}
          sparklineData={countriesSparkline}
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
