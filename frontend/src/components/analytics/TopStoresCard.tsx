// ABOUTME: Displays top 10 stores by revenue with location details
// ABOUTME: Shows store name, city, country, revenue, units, and transactions
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Store, MapPin } from 'lucide-react'

interface TopStoresCardProps {
  data: Array<{
    store_id: string
    store_name: string
    city: string
    country: string
    revenue: number
    units: number
    transactions: number
  }>
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

const formatCompact = (value: number) => {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`
  }
  return value.toString()
}

export function TopStoresCard({ data }: TopStoresCardProps) {
  const maxRevenue = Math.max(...data.map(s => s.revenue))

  return (
    <Card className="border-border bg-card shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary/10 to-accent/10 flex items-center justify-center border border-primary/20">
            <Store className="h-5 w-5 text-primary" />
          </div>
          Top Stores
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data.map((store, index) => {
            const percentage = (store.revenue / maxRevenue) * 100

            return (
              <div key={store.store_id} className="space-y-2">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className="flex items-center justify-center h-8 w-8 rounded-full bg-primary/10 text-primary font-bold text-sm shrink-0">
                      {index + 1}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-sm truncate">{store.store_name}</p>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        <span className="truncate">{store.city}, {store.country}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatCompact(store.units)} units • {store.transactions} transactions
                      </p>
                    </div>
                  </div>
                  <p className="font-bold text-sm shrink-0">{formatCurrency(store.revenue)}</p>
                </div>

                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
