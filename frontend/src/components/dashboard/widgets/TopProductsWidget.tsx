import { useKPIs } from '@/api/analytics'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { TrendingUp, Package, ArrowUpRight } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { useNavigate } from 'react-router-dom'
import type { WidgetConfig } from '@/types/dashboardConfig'

interface TopProductsWidgetProps {
  config: WidgetConfig
}

export function TopProductsWidget({ config }: TopProductsWidgetProps) {
  const navigate = useNavigate()
  const { data: kpis, isLoading } = useKPIs()
  const limit = config.props.limit || 5

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="border-b border-border bg-background/50">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <TrendingUp className="h-4 w-4 text-primary" />
              </div>
              {config.props.title || 'Top Products'}
            </CardTitle>
            <CardDescription className="mt-1.5">
              {config.props.description || 'Best performing products by revenue'}
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
          ) : kpis?.top_products && kpis.top_products.length > 0 ? (
            kpis.top_products.slice(0, limit).map((product, idx) => (
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
                      <span className="font-semibold">
                        {((product.revenue / (kpis?.total_revenue || 1)) * 100).toFixed(1)}%
                      </span>
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
  )
}
