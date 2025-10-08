import type { Dashboard } from '@/types'
import { Card } from '@/components/ui/card'

interface DashboardIframeProps {
  dashboard: Dashboard
}

export function DashboardIframe({ dashboard }: DashboardIframeProps) {
  return (
    <Card className="overflow-hidden border-0 shadow-lg">
      <iframe
        src={dashboard.dashboard_url}
        title={dashboard.dashboard_name}
        className="h-[calc(100vh-12rem)] w-full"
        sandbox="allow-scripts allow-same-origin allow-forms"
        loading="lazy"
      />
    </Card>
  )
}
