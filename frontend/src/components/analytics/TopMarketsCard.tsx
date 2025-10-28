// ABOUTME: Displays top 7 markets (countries) by revenue
// ABOUTME: Shows revenue, units, and transaction counts for each country
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Globe } from 'lucide-react'

interface TopMarketsCardProps {
  data: Array<{
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

export function TopMarketsCard({ data }: TopMarketsCardProps) {
  const maxRevenue = Math.max(...data.map(m => m.revenue))

  return (
    <Card className="border-border bg-card shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary/10 to-accent/10 flex items-center justify-center border border-primary/20">
            <Globe className="h-5 w-5 text-primary" />
          </div>
          Top Markets
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data.map((market, index) => {
            const percentage = (market.revenue / maxRevenue) * 100

            return (
              <div key={market.country} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center h-8 w-8 rounded-full bg-primary/10 text-primary font-bold text-sm">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-semibold text-sm">{market.country}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatCompact(market.units)} units • {market.transactions} transactions
                      </p>
                    </div>
                  </div>
                  <p className="font-bold text-sm">{formatCurrency(market.revenue)}</p>
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
