/**
 * Dashboard Selector Component
 *
 * Provides a dropdown interface for switching between available dashboards.
 * Features:
 * - Lists all user dashboards + tenant-wide templates
 * - Shows dashboard descriptions
 * - Highlights default dashboards
 * - Persists selection in localStorage
 * - Responsive design
 */

import { useState, useEffect } from 'react'
import { Select, SelectOption } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Plus, LayoutDashboard } from 'lucide-react'
import { useDashboardConfigList } from '@/api/dashboardConfig'
import { CreateDashboardDialog } from './CreateDashboardDialog'
import { cn } from '@/lib/utils'

const DASHBOARD_STORAGE_KEY = 'taskifai_selected_dashboard_id'

interface DashboardSelectorProps {
  selectedDashboardId?: string
  onDashboardChange: (dashboardId: string) => void
  className?: string
}

export function DashboardSelector({
  selectedDashboardId,
  onDashboardChange,
  className,
}: DashboardSelectorProps) {
  const { data: response, isLoading } = useDashboardConfigList(true)
  const [selectedId, setSelectedId] = useState<string | undefined>(selectedDashboardId)
  const [showCreateDialog, setShowCreateDialog] = useState(false)

  // Sync with parent prop
  useEffect(() => {
    if (selectedDashboardId && selectedDashboardId !== selectedId) {
      setSelectedId(selectedDashboardId)
    }
  }, [selectedDashboardId])

  // Load from localStorage on mount
  useEffect(() => {
    if (!selectedId && response?.dashboards.length) {
      const storedId = localStorage.getItem(DASHBOARD_STORAGE_KEY)
      if (storedId) {
        // Verify stored ID exists in available dashboards
        const exists = response.dashboards.find(d => d.dashboard_id === storedId)
        if (exists) {
          setSelectedId(storedId)
          onDashboardChange(storedId)
          return
        }
      }

      // Fall back to default dashboard
      const defaultDashboard = response.dashboards.find(d => d.is_default)
      if (defaultDashboard) {
        setSelectedId(defaultDashboard.dashboard_id)
        onDashboardChange(defaultDashboard.dashboard_id)
      }
    }
  }, [response?.dashboards, selectedId, onDashboardChange])

  const handleChange = (dashboardId: string) => {
    setSelectedId(dashboardId)
    localStorage.setItem(DASHBOARD_STORAGE_KEY, dashboardId)
    onDashboardChange(dashboardId)
  }

  if (isLoading || !response) {
    return (
      <div className="flex items-center gap-3 animate-pulse">
        <div className="h-10 w-64 bg-muted rounded-md" />
        <div className="h-10 w-32 bg-muted rounded-md" />
      </div>
    )
  }

  const dashboards = response.dashboards || []

  // Convert dashboards to select options
  const options: SelectOption[] = dashboards
    .sort((a, b) => {
      // Default first, then by display_order, then by name
      if (a.is_default && !b.is_default) return -1
      if (!a.is_default && b.is_default) return 1
      if (a.display_order !== b.display_order) return a.display_order - b.display_order
      return a.dashboard_name.localeCompare(b.dashboard_name)
    })
    .map(dashboard => ({
      value: dashboard.dashboard_id,
      label: dashboard.dashboard_name,
      disabled: false,
    }))

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      {/* Dashboard Selector Bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 max-w-[200px]">
          <LayoutDashboard className="h-5 w-5 text-muted-foreground" />
          <Select
            options={options}
            value={selectedId}
            onValueChange={handleChange}
            placeholder="Select a dashboard..."
            className="w-full"
          />
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowCreateDialog(true)}
          className="whitespace-nowrap"
        >
          <Plus className="h-4 w-4" />
          New Dashboard
        </Button>
      </div>

      {/* Dashboard Count */}
      <p className="text-xs text-muted-foreground">
        {dashboards.length} {dashboards.length === 1 ? 'dashboard' : 'dashboards'} available
        {response.has_default && ' (including default)'}
      </p>

      {/* Create Dashboard Dialog */}
      <CreateDashboardDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSuccess={(newDashboardId) => {
          handleChange(newDashboardId)
        }}
      />
    </div>
  )
}
