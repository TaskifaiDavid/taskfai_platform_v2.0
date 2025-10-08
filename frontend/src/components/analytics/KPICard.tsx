import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Sparkline } from '@/components/ui/sparkline'
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface KPICardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: {
    value: number
    isPositive: boolean
  }
  sparklineData?: number[]
  subtitle?: string
  className?: string
}

export function KPICard({ title, value, icon: Icon, trend, sparklineData, subtitle, className }: KPICardProps) {
  return (
    <Card className={cn("border-border bg-card shadow-sm group overflow-hidden relative", className)}>
      {/* Gradient overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3 relative z-10">
        <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          {title}
        </CardTitle>
        <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-primary/10 to-accent/10 flex items-center justify-center group-hover:from-primary/20 group-hover:to-accent/20 group-hover:scale-110 transition-all duration-300 border border-primary/20">
          <Icon className="h-5 w-5 text-primary" />
        </div>
      </CardHeader>
      <CardContent className="relative z-10">
        <div className="space-y-3">
          <div className="text-3xl font-bold tracking-tight text-foreground">
            {value}
          </div>

          {/* Sparkline Chart - Using Teal color */}
          {sparklineData && sparklineData.length > 0 && (
            <div className="h-12 -mx-2 opacity-80 group-hover:opacity-100 transition-opacity">
              <Sparkline
                data={sparklineData}
                color="hsl(var(--accent))"
              />
            </div>
          )}

          {subtitle && (
            <p className="text-sm text-muted-foreground">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center gap-2 pt-1">
              <div className={cn(
                "flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold shadow-sm border",
                trend.isPositive
                  ? "bg-success/10 text-success border-success/30"
                  : "bg-destructive/10 text-destructive border-destructive/30"
              )}>
                {trend.isPositive ? (
                  <TrendingUp className="h-3.5 w-3.5" />
                ) : (
                  <TrendingDown className="h-3.5 w-3.5" />
                )}
                <span>{trend.isPositive ? '+' : ''}{trend.value}%</span>
              </div>
              <span className="text-xs text-muted-foreground font-medium">vs last period</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
