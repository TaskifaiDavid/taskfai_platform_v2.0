// ABOUTME: Horizontal bar chart displaying top 10 resellers by revenue
// ABOUTME: Used in Analytics dashboard to visualize reseller performance
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Users } from 'lucide-react'

interface TopResellersChartProps {
  data: Array<{
    reseller_id: string
    reseller_name: string
    revenue: number
    units: number
    transactions: number
    store_count: number
  }>
}

const COLORS = [
  'hsl(var(--primary))',
  'hsl(var(--accent))',
  'hsl(var(--primary) / 0.8)',
  'hsl(var(--accent) / 0.8)',
  'hsl(var(--primary) / 0.6)',
  'hsl(var(--accent) / 0.6)',
  'hsl(var(--primary) / 0.4)',
  'hsl(var(--accent) / 0.4)',
  'hsl(var(--primary) / 0.3)',
  'hsl(var(--accent) / 0.3)',
]

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
        <p className="font-semibold text-sm mb-2">{data.reseller_name}</p>
        <div className="space-y-1 text-xs">
          <p className="font-bold text-primary">{formatCurrency(data.revenue)}</p>
          <p className="text-muted-foreground">{data.units.toLocaleString()} units sold</p>
          <p className="text-muted-foreground">{data.transactions} transactions</p>
          <p className="text-muted-foreground">{data.store_count} stores</p>
        </div>
      </div>
    )
  }
  return null
}

export function TopResellersChart({ data }: TopResellersChartProps) {
  const chartData = data.map(item => ({
    ...item,
    name: item.reseller_name.length > 30
      ? item.reseller_name.substring(0, 30) + '...'
      : item.reseller_name
  }))

  return (
    <Card className="border-border bg-card shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary/10 to-accent/10 flex items-center justify-center border border-primary/20">
            <Users className="h-5 w-5 text-primary" />
          </div>
          Top 10 Resellers by Revenue
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              type="number"
              tickFormatter={formatCurrency}
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
            />
            <YAxis
              type="category"
              dataKey="name"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              width={90}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="revenue" radius={[0, 8, 8, 0]}>
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
