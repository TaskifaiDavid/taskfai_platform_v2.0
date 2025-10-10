import { useKPIs } from '@/api/analytics'
import { KPICard } from '@/components/analytics/KPICard'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Euro, Package, TrendingUp, Upload as UploadIcon } from 'lucide-react'
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

      {kpiList.includes('total_uploads') && kpis && (
        <KPICard
          title="Total Uploads"
          value={kpis.total_uploads || 0}
          icon={UploadIcon}
          sparklineData={uploadsSparkline}
          className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      )}
    </div>
  )
}
