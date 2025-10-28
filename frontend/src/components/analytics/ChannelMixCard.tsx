// ABOUTME: Displays revenue and units breakdown by sales channel
// ABOUTME: Shows percentage distribution across online, retail, and B2B channels
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Laptop, Store, Building2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChannelMixCardProps {
  data: Array<{
    channel: string
    revenue: number
    revenue_percentage: number
    units: number
    units_percentage: number
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

const getChannelIcon = (channel: string) => {
  switch (channel.toLowerCase()) {
    case 'online':
      return Laptop
    case 'retail':
      return Store
    case 'b2b':
      return Building2
    default:
      return Store
  }
}

const getChannelColor = (index: number) => {
  const colors = [
    'text-primary bg-primary/10 border-primary/30',
    'text-accent bg-accent/10 border-accent/30',
    'text-purple-600 bg-purple-100 border-purple-300'
  ]
  return colors[index % colors.length]
}

export function ChannelMixCard({ data }: ChannelMixCardProps) {
  return (
    <Card className="border-border bg-card shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">Channel Mix</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data.map((channel, index) => {
            const Icon = getChannelIcon(channel.channel)
            const colorClass = getChannelColor(index)

            return (
              <div key={channel.channel} className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "h-10 w-10 rounded-lg flex items-center justify-center border",
                      colorClass
                    )}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-semibold capitalize">{channel.channel}</p>
                      <p className="text-xs text-muted-foreground">{channel.transactions} transactions</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-sm">{formatCurrency(channel.revenue)}</p>
                    <p className="text-xs text-muted-foreground">{channel.units.toLocaleString()} units</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Revenue</span>
                      <span className="font-semibold">{channel.revenue_percentage.toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={cn("h-full transition-all duration-500",
                          index === 0 ? "bg-primary" : index === 1 ? "bg-accent" : "bg-purple-600"
                        )}
                        style={{ width: `${channel.revenue_percentage}%` }}
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Units</span>
                      <span className="font-semibold">{channel.units_percentage.toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={cn("h-full transition-all duration-500",
                          index === 0 ? "bg-primary/70" : index === 1 ? "bg-accent/70" : "bg-purple-600/70"
                        )}
                        style={{ width: `${channel.units_percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
