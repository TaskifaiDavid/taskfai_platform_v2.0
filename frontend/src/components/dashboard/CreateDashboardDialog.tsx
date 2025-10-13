/**
 * Create Dashboard Dialog Component
 *
 * Modal dialog for creating new custom dashboards.
 * Features:
 * - Dashboard name input (required)
 * - Optional description
 * - Copy from existing template option
 * - Form validation
 * - Loading states
 */

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Select, SelectOption } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, Loader2 } from 'lucide-react'
import { useCreateDashboardConfig, useDashboardConfigList } from '@/api/dashboardConfig'
import type { DashboardConfigCreate } from '@/types/dashboardConfig'
import { WidgetType, KPIType } from '@/types/dashboardConfig'

interface CreateDashboardDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: (dashboardId: string) => void
}

export function CreateDashboardDialog({
  open,
  onOpenChange,
  onSuccess,
}: CreateDashboardDialogProps) {
  const [dashboardName, setDashboardName] = useState('')
  const [description, setDescription] = useState('')
  const [templateId, setTemplateId] = useState<string>('')
  const [nameError, setNameError] = useState('')

  const { data: templatesResponse } = useDashboardConfigList(true)
  const createDashboard = useCreateDashboardConfig()

  // Reset form when dialog opens/closes
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setDashboardName('')
      setDescription('')
      setTemplateId('')
      setNameError('')
      createDashboard.reset()
    }
    onOpenChange(newOpen)
  }

  // Form validation
  const validateName = (name: string): boolean => {
    const trimmedName = name.trim()
    if (!trimmedName) {
      setNameError('Dashboard name is required')
      return false
    }
    if (trimmedName.length > 100) {
      setNameError('Dashboard name must be 100 characters or less')
      return false
    }
    setNameError('')
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validate form
    if (!validateName(dashboardName)) {
      return
    }

    try {
      // Get template dashboard if selected
      let config: DashboardConfigCreate

      if (templateId && templatesResponse) {
        // Find the template dashboard
        const template = templatesResponse.dashboards.find(
          d => d.dashboard_id === templateId
        )

        if (template) {
          // TODO: Fetch full template config to copy layout/kpis
          // For now, create with default KPI widget
          config = {
            dashboard_name: dashboardName.trim(),
            description: description.trim() || undefined,
            layout: [
              {
                id: 'kpi-grid-1',
                type: WidgetType.KPI_GRID,
                position: { row: 0, col: 0, width: 12, height: 2 },
                props: {
                  kpis: [KPIType.TOTAL_REVENUE, KPIType.TOTAL_UNITS, KPIType.AVG_PRICE, KPIType.TOTAL_UPLOADS]
                }
              }
            ],
            kpis: [KPIType.TOTAL_REVENUE, KPIType.TOTAL_UNITS, KPIType.AVG_PRICE, KPIType.TOTAL_UPLOADS],
            filters: {
              date_range: 'last_30_days',
              vendor: 'all',
            },
            is_default: false,
            is_active: true,
          }
        } else {
          throw new Error('Selected template not found')
        }
      } else {
        // Create dashboard with default KPI widget (prevents 422 validation error)
        config = {
          dashboard_name: dashboardName.trim(),
          description: description.trim() || undefined,
          layout: [
            {
              id: 'kpi-grid-1',
              type: WidgetType.KPI_GRID,
              position: { row: 0, col: 0, width: 12, height: 2 },
              props: {
                kpis: [KPIType.TOTAL_REVENUE, KPIType.TOTAL_UNITS, KPIType.AVG_PRICE, KPIType.TOTAL_UPLOADS]
              }
            }
          ],
          kpis: [KPIType.TOTAL_REVENUE, KPIType.TOTAL_UNITS, KPIType.AVG_PRICE, KPIType.TOTAL_UPLOADS],
          filters: {
            date_range: 'last_30_days',
            vendor: 'all',
          },
          is_default: false,
          is_active: true,
        }
      }

      // Create dashboard via API
      const result = await createDashboard.mutateAsync(config)

      // Success - notify parent and close dialog
      onSuccess?.(result.dashboard_id)
      handleOpenChange(false)
    } catch (error) {
      // Error is handled by mutation's error state
      console.error('Failed to create dashboard:', error)
    }
  }

  // Convert templates to select options
  const templateOptions: SelectOption[] = [
    { value: '', label: 'Blank Dashboard', disabled: false },
    ...(templatesResponse?.dashboards || [])
      .filter(d => d.is_active)
      .map(d => ({
        value: d.dashboard_id,
        label: `${d.dashboard_name} (${d.widget_count} widgets, ${d.kpi_count} KPIs)`,
        disabled: false,
      })),
  ]

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent onClose={() => handleOpenChange(false)} className="max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Dashboard</DialogTitle>
            <DialogDescription>
              Create a custom dashboard from scratch or copy an existing template.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Dashboard Name */}
            <div className="space-y-2">
              <Label htmlFor="dashboard-name">
                Dashboard Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="dashboard-name"
                placeholder="e.g., Sales Analytics Dashboard"
                value={dashboardName}
                onChange={(e) => {
                  setDashboardName(e.target.value)
                  if (nameError) validateName(e.target.value)
                }}
                onBlur={() => validateName(dashboardName)}
                maxLength={100}
                disabled={createDashboard.isPending}
                className={nameError ? 'border-destructive' : ''}
              />
              {nameError && (
                <p className="text-xs text-destructive">{nameError}</p>
              )}
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="dashboard-description">Description (Optional)</Label>
              <Textarea
                id="dashboard-description"
                placeholder="Describe the purpose of this dashboard..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={500}
                rows={3}
                disabled={createDashboard.isPending}
              />
              <p className="text-xs text-muted-foreground">
                {description.length}/500 characters
              </p>
            </div>

            {/* Template Selection */}
            <div className="space-y-2">
              <Label htmlFor="template">Copy From Template</Label>
              <Select
                options={templateOptions}
                value={templateId}
                onValueChange={setTemplateId}
                placeholder="Select a template..."
                disabled={createDashboard.isPending}
              />
              <p className="text-xs text-muted-foreground">
                {templateId
                  ? 'Dashboard will be created with the selected template\'s layout and KPIs'
                  : 'Start with an empty dashboard'}
              </p>
            </div>

            {/* Error Alert */}
            {createDashboard.isError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Failed to create dashboard. Please try again.
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={createDashboard.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createDashboard.isPending}>
              {createDashboard.isPending && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              Create Dashboard
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
