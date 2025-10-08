import { useState } from 'react'
import { useKPIs, useSalesData } from '@/api/analytics'
import { KPICard } from '@/components/analytics/KPICard'
import { SalesTable } from '@/components/analytics/SalesTable'
import { ExportButton } from '@/components/analytics/ExportButton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Euro, Package, TrendingUp, Users, BarChart3, Calendar } from 'lucide-react'

export function Analytics() {
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const { data: kpis } = useKPIs(dateFrom, dateTo)
  const { data: salesData } = useSalesData({
    date_from: dateFrom,
    date_to: dateTo,
    page: 1,
    page_size: 50,
  })

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <div className="space-y-8 animate-in fade-in-0 duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center border border-primary/30 shadow-sm">
            <BarChart3 className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Analytics</h1>
            <p className="text-sm text-muted-foreground mt-1">Comprehensive sales analytics and detailed reporting</p>
          </div>
        </div>
        <ExportButton dateFrom={dateFrom} dateTo={dateTo} />
      </div>

      {/* Date Filters */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader className="border-b border-border bg-background/50">
          <CardTitle className="flex items-center gap-2 text-lg">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Calendar className="h-4 w-4 text-primary" />
            </div>
            Date Range
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="dateFrom" className="text-xs uppercase tracking-wide font-semibold text-muted-foreground">
                From
              </Label>
              <Input
                id="dateFrom"
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="border-border focus:border-primary focus:ring-primary"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dateTo" className="text-xs uppercase tracking-wide font-semibold text-muted-foreground">
                To
              </Label>
              <Input
                id="dateTo"
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="border-border focus:border-primary focus:ring-primary"
              />
            </div>
            <div className="flex items-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => { setDateFrom(''); setDateTo(''); }}
                className="border-border hover:border-primary hover:text-primary"
              >
                Clear
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={() => {
                  const today = new Date();
                  const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
                  setDateFrom(lastMonth.toISOString().split('T')[0]);
                  setDateTo(today.toISOString().split('T')[0]);
                }}
                className="bg-primary hover:bg-primary/90"
              >
                Last 30 Days
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPIs */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Revenue"
          value={kpis ? formatCurrency(kpis.total_revenue) : '€0'}
          icon={Euro}
          subtitle="All channels"
          className="hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
        <KPICard
          title="Total Units"
          value={kpis?.total_units.toLocaleString() || '0'}
          icon={Package}
          subtitle="Items sold"
          className="hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
        <KPICard
          title="Average Price"
          value={kpis ? formatCurrency(kpis.avg_price) : '€0'}
          icon={TrendingUp}
          subtitle="Per unit"
          className="hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
        <KPICard
          title="Resellers"
          value={kpis?.top_resellers.length || 0}
          icon={Users}
          subtitle="Active partners"
          className="hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
        />
      </div>

      {/* Sales Table */}
      {salesData && salesData.sales.length > 0 && (
        <SalesTable
          sales={salesData.sales}
          title="Detailed Sales"
          description={`Showing ${salesData.sales.length} of ${salesData.total} sales`}
        />
      )}
    </div>
  )
}
