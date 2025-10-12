/**
 * Dashboard Page - Now uses dynamic database-driven configuration
 * Option 1: Database-Driven Dashboards Implementation
 *
 * Features:
 * - Dashboard selector dropdown
 * - Dynamic dashboard loading based on selection
 * - localStorage persistence for selected dashboard
 */

import { useState } from 'react'
import { DynamicDashboard } from '@/components/dashboard/DynamicDashboard'
import { DashboardSelector } from '@/components/dashboard/DashboardSelector'
import { useDashboardConfigById } from '@/api/dashboardConfig'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'

export function Dashboard() {
  const [selectedDashboardId, setSelectedDashboardId] = useState<string>()

  // Fetch selected dashboard config
  const { data: config, isLoading, error } = useDashboardConfigById(selectedDashboardId || null)

  const handleDashboardChange = (dashboardId: string) => {
    setSelectedDashboardId(dashboardId)
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Selector */}
      <DashboardSelector
        selectedDashboardId={selectedDashboardId}
        onDashboardChange={handleDashboardChange}
      />

      {/* Dashboard Content */}
      {isLoading && (
        <div className="space-y-6">
          <Skeleton className="h-12 w-full bg-muted" />
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-32 w-full bg-muted" />
            ))}
          </div>
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load dashboard configuration. Please try selecting a different dashboard.
          </AlertDescription>
        </Alert>
      )}

      {!isLoading && !error && config && (
        <DynamicDashboard config={config} />
      )}
    </div>
  )
}
