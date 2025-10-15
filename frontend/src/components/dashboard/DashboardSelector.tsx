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
import { useNavigate } from 'react-router-dom'
import { Select, SelectOption } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Plus, LayoutDashboard, Sparkles, Pencil, Trash2, AlertTriangle } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { useDashboardConfigList, useDeleteDashboardConfig } from '@/api/dashboardConfig'
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
  const navigate = useNavigate()
  const { data: response, isLoading } = useDashboardConfigList(true)
  const deleteDashboard = useDeleteDashboardConfig()
  const [selectedId, setSelectedId] = useState<string | undefined>(selectedDashboardId)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

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

  const handleEdit = () => {
    if (selectedId) {
      navigate(`/dashboard/builder?edit=${selectedId}`)
    }
  }

  const handleDelete = async () => {
    if (!selectedId) return

    try {
      await deleteDashboard.mutateAsync(selectedId)
      setShowDeleteDialog(false)

      // Clear selection and localStorage
      setSelectedId(undefined)
      localStorage.removeItem(DASHBOARD_STORAGE_KEY)

      // Select first available dashboard or undefined
      if (response?.dashboards.length) {
        const nextDashboard = response.dashboards.find(d => d.dashboard_id !== selectedId)
        if (nextDashboard) {
          handleChange(nextDashboard.dashboard_id)
        }
      }
    } catch (error) {
      console.error('Failed to delete dashboard:', error)
    }
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
          onClick={handleEdit}
          disabled={!selectedId}
          className="whitespace-nowrap"
        >
          <Pencil className="h-4 w-4 mr-2" />
          Edit
        </Button>

        <Button
          variant="default"
          size="sm"
          onClick={() => navigate('/dashboard/builder')}
          className="whitespace-nowrap"
        >
          <Sparkles className="h-4 w-4 mr-2" />
          Build New
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowCreateDialog(true)}
          className="whitespace-nowrap"
        >
          <Plus className="h-4 w-4 mr-2" />
          Quick Add
        </Button>

        <Button
          variant="destructive"
          size="sm"
          onClick={() => setShowDeleteDialog(true)}
          disabled={!selectedId || dashboards.find(d => d.dashboard_id === selectedId)?.is_default}
          className="whitespace-nowrap"
        >
          <Trash2 className="h-4 w-4" />
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

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent onClose={() => setShowDeleteDialog(false)}>
          <DialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="h-10 w-10 rounded-full bg-destructive/10 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-destructive" />
              </div>
              <DialogTitle>Delete Dashboard</DialogTitle>
            </div>
            <DialogDescription>
              Are you sure you want to delete this dashboard? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={deleteDashboard.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteDashboard.isPending}
            >
              {deleteDashboard.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
