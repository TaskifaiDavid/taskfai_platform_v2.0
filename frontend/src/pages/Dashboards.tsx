import { useDashboards } from '@/api/dashboards'
import { DashboardIframe } from '@/components/dashboard/DashboardIframe'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, Monitor } from 'lucide-react'

export function Dashboards() {
  const { data: dashboards, isLoading } = useDashboards()

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-10rem)] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  const primaryDashboard = dashboards?.find((d) => d.is_primary)

  if (!dashboards || dashboards.length === 0) {
    return (
      <div className="space-y-8 animate-in fade-in-0 duration-500">
        {/* Header */}
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center border border-primary/30 shadow-sm">
            <Monitor className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Dashboards</h1>
            <p className="text-sm text-muted-foreground mt-1">Embedded analytics dashboards</p>
          </div>
        </div>

        <Card className="border-border bg-card shadow-sm">
          <CardContent className="flex flex-col items-center justify-center p-16">
            <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center border border-primary/30 shadow-lg mb-6">
              <Monitor className="h-10 w-10 text-primary" />
            </div>
            <p className="text-xl font-semibold text-foreground mb-2">No dashboards configured</p>
            <p className="text-sm text-muted-foreground">
              Contact your administrator to set up dashboard access
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-in fade-in-0 duration-500">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center border border-primary/30 shadow-sm">
          <Monitor className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">Dashboards</h1>
          <p className="text-sm text-muted-foreground mt-1">Embedded analytics dashboards</p>
        </div>
      </div>

      {primaryDashboard && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold">{primaryDashboard.dashboard_name}</h2>
            <Badge className="bg-primary text-primary-foreground border-0 shadow-sm">Primary</Badge>
          </div>
          <DashboardIframe dashboard={primaryDashboard} />
        </div>
      )}

      {dashboards.filter((d) => !d.is_primary).length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Other Dashboards</h2>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {dashboards
              .filter((d) => !d.is_primary)
              .map((dashboard) => (
                <Card
                  key={dashboard.config_id}
                  className="cursor-pointer border-border bg-card hover:shadow-lg hover:scale-[1.02] transition-all duration-200"
                >
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Monitor className="h-5 w-5 text-primary" />
                      {dashboard.dashboard_name}
                    </CardTitle>
                    <CardDescription className="capitalize">
                      {dashboard.dashboard_type}
                    </CardDescription>
                  </CardHeader>
                </Card>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
