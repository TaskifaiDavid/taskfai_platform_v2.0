import { useKPIs } from '@/api/analytics'
import { useUploadsList } from '@/api/uploads'
import { KPICard } from '@/components/analytics/KPICard'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { Euro, Package, TrendingUp, Upload as UploadIcon, ArrowUpRight, Clock, Sparkles } from 'lucide-react'
import { UploadStatus } from '@/components/upload/UploadStatus'
import { Skeleton } from '@/components/ui/skeleton'
import { useNavigate } from 'react-router-dom'

export function Dashboard() {
  const navigate = useNavigate()
  const { data: kpis, isLoading: kpisLoading } = useKPIs()
  const { data: uploads, isLoading: uploadsLoading } = useUploadsList()
  const recentUploads = uploads?.slice(0, 5) || []

  // Generate sparkline data (mock data for demo - would come from API in production)
  const revenueSparkline = [42000, 45000, 43500, 47000, 49000, 48500, 52000, 54000, 53000, 56000, 58000, 60000]
  const unitsSparkline = [850, 920, 880, 950, 1020, 990, 1080, 1150, 1120, 1200, 1280, 1320]
  const priceSparkline = [48, 49, 47, 50, 48, 49, 48, 47, 47, 47, 45, 45]
  const uploadsSparkline = [2, 3, 2, 4, 3, 5, 4, 6, 5, 7, 6, uploads?.length || 8]

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <div className="space-y-8 animate-in fade-in-0 slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-4xl font-bold tracking-tight">Dashboard</h1>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-success/10 border border-success/30">
                <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
                <span className="text-xs font-semibold text-success">Live</span>
              </div>
            </div>
            <p className="text-base text-muted-foreground">Real-time overview of your sales performance and key metrics</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="border-border hover:border-primary hover:text-primary">
              <Clock className="h-4 w-4 mr-2" />
              Last 30 days
            </Button>
          </div>
        </div>
      </div>

      {/* KPIs Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {kpisLoading ? (
          <>
            {[...Array(4)].map((_, i) => (
              <Card key={i} className="border-border bg-card shadow-sm animate-pulse">
                <CardContent className="pt-6">
                  <Skeleton className="h-28 w-full bg-muted" />
                </CardContent>
              </Card>
            ))}
          </>
        ) : (
          <>
            <KPICard
              title="Total Revenue"
              value={kpis ? formatCurrency(kpis.total_revenue) : '€0'}
              icon={Euro}
              trend={{ value: 12.5, isPositive: true }}
              sparklineData={revenueSparkline}
              className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
            />
            <KPICard
              title="Total Units Sold"
              value={kpis?.total_units.toLocaleString() || '0'}
              icon={Package}
              trend={{ value: 8.2, isPositive: true }}
              sparklineData={unitsSparkline}
              className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
            />
            <KPICard
              title="Average Price"
              value={kpis ? formatCurrency(kpis.avg_price) : '€0'}
              icon={TrendingUp}
              trend={{ value: 3.1, isPositive: false }}
              sparklineData={priceSparkline}
              className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
            />
            <KPICard
              title="Total Uploads"
              value={uploads?.length || 0}
              icon={UploadIcon}
              sparklineData={uploadsSparkline}
              className="border-border bg-card hover:shadow-md transition-all duration-200 hover:scale-[1.02]"
            />
          </>
        )}
      </div>

      {/* Content Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Uploads */}
        <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="border-b border-border bg-background/50">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <div className="h-8 w-8 rounded-lg bg-accent/10 flex items-center justify-center">
                    <Clock className="h-4 w-4 text-accent" />
                  </div>
                  Recent Uploads
                </CardTitle>
                <CardDescription className="mt-1.5">Latest file uploads and processing status</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/uploads')}
                className="hover:bg-accent/10 hover:text-accent"
              >
                View all
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-3">
              {uploadsLoading ? (
                <>
                  {[...Array(3)].map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full bg-muted" />
                  ))}
                </>
              ) : recentUploads.length > 0 ? (
                recentUploads.map((upload) => (
                  <div
                    key={upload.batch_id}
                    className="flex items-center justify-between rounded-lg border border-border p-4 hover:bg-background/80 hover:border-primary/50 transition-all duration-200 group cursor-pointer"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold truncate group-hover:text-primary transition-colors">
                        {upload.filename}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(upload.uploaded_at).toLocaleString()}
                      </p>
                    </div>
                    <UploadStatus status={upload.status} />
                  </div>
                ))
              ) : (
                <EmptyState
                  icon={UploadIcon}
                  title="No uploads yet"
                  description="Upload your first file to get started with analytics"
                  action={{
                    label: "Go to Uploads",
                    onClick: () => navigate('/uploads')
                  }}
                />
              )}
            </div>
          </CardContent>
        </Card>

        {/* Top Products */}
        <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="border-b border-border bg-background/50">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                    <TrendingUp className="h-4 w-4 text-primary" />
                  </div>
                  Top Products
                </CardTitle>
                <CardDescription className="mt-1.5">Best performing products by revenue</CardDescription>
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
              {kpisLoading ? (
                <>
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full bg-muted" />
                  ))}
                </>
              ) : kpis?.top_products && kpis.top_products.length > 0 ? (
                kpis.top_products.slice(0, 5).map((product, idx) => (
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
                          {product.product_name}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {product.units.toLocaleString()} units sold
                        </p>
                      </div>
                    </div>
                    <div className="text-right flex items-center gap-3">
                      <div>
                        <p className="text-sm font-bold text-foreground">{formatCurrency(product.revenue)}</p>
                        <div className="flex items-center gap-1 text-xs text-success mt-1">
                          <ArrowUpRight className="h-3 w-3" />
                          <span className="font-semibold">{((product.revenue / (kpis?.total_revenue || 1)) * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <EmptyState
                  icon={Package}
                  title="No sales data yet"
                  description="Upload sales data to see your top performing products"
                  action={{
                    label: "Upload Data",
                    onClick: () => navigate('/uploads')
                  }}
                />
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
