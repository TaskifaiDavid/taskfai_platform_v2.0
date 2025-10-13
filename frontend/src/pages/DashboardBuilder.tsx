/**
 * Dashboard Builder Page
 *
 * Visual dashboard builder interface
 * Allows customers to create and configure custom dashboards
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  ArrowLeft,
  Save,
  Eye,
  Plus,
  Trash2,
  GripVertical,
  AlertCircle,
  CheckCircle,
  Layers
} from 'lucide-react'
import { WidgetGallery } from '@/components/dashboard/builder/WidgetGallery'
import { WidgetConfigForm } from '@/components/dashboard/builder/WidgetConfigForm'
import { DynamicDashboard } from '@/components/dashboard/DynamicDashboard'
import type { WidgetMetadata } from '@/types/widgetBuilder'
import type { WidgetConfig, DashboardConfig, KPIType } from '@/types/dashboardConfig'
import { useCreateDashboardConfig } from '@/api/dashboardConfig'

export function DashboardBuilder() {
  const navigate = useNavigate()
  const createDashboard = useCreateDashboardConfig()

  // Builder state
  const [dashboardName, setDashboardName] = useState('My Custom Dashboard')
  const [description, setDescription] = useState('')
  const [isDefault, setIsDefault] = useState(false)
  const [widgets, setWidgets] = useState<WidgetConfig[]>([])

  // UI state
  const [selectedTab, setSelectedTab] = useState<'build' | 'preview'>('build')
  const [editingWidget, setEditingWidget] = useState<WidgetConfig | null>(null)
  const [showWidgetGallery, setShowWidgetGallery] = useState(true)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)

  const handleSelectWidget = (metadata: WidgetMetadata) => {
    // Create new widget with default config
    // All configuration goes in 'props' per backend schema
    const newWidget: WidgetConfig = {
      id: crypto.randomUUID(),
      type: metadata.type,
      position: { row: widgets.length, col: 0, width: 12, height: 4 },
      props: {
        title: metadata.name,
        dateRange: 'last_30_days'
      }
    }

    setEditingWidget(newWidget)
    setShowWidgetGallery(false)
  }

  const handleSaveWidget = (config: WidgetConfig) => {
    if (widgets.find(w => w.id === config.id)) {
      // Update existing widget
      setWidgets(prev => prev.map(w => w.id === config.id ? config : w))
    } else {
      // Add new widget
      setWidgets(prev => [...prev, config])
    }

    setEditingWidget(null)
    setShowWidgetGallery(true)
  }

  const handleEditWidget = (widget: WidgetConfig) => {
    setEditingWidget(widget)
    setShowWidgetGallery(false)
  }

  const handleDeleteWidget = (widgetId: string) => {
    setWidgets(prev => prev.filter(w => w.id !== widgetId))
  }

  const handleMoveWidget = (widgetId: string, direction: 'up' | 'down') => {
    const index = widgets.findIndex(w => w.id === widgetId)
    if (index === -1) return

    const newWidgets = [...widgets]
    const targetIndex = direction === 'up' ? index - 1 : index + 1

    if (targetIndex < 0 || targetIndex >= widgets.length) return

    // Swap widgets
    [newWidgets[index], newWidgets[targetIndex]] = [newWidgets[targetIndex], newWidgets[index]]

    // Update positions
    newWidgets.forEach((w, i) => {
      w.position.row = i
    })

    setWidgets(newWidgets)
  }

  const handleSaveDashboard = async () => {
    // Validation
    if (!dashboardName.trim()) {
      setSaveError('Dashboard name is required')
      return
    }

    if (widgets.length === 0) {
      setSaveError('Please add at least one widget to your dashboard')
      return
    }

    setSaveError(null)
    setSaveSuccess(false)

    try {
      // Extract KPI types from widgets
      const kpis: KPIType[] = []
      widgets.forEach(widget => {
        if (widget.props?.dataSource) {
          if (Array.isArray(widget.props.dataSource)) {
            kpis.push(...widget.props.dataSource as KPIType[])
          } else {
            kpis.push(widget.props.dataSource as KPIType)
          }
        }
      })

      // Build dashboard configuration
      const dashboardConfig = {
        dashboard_name: dashboardName,
        description: description || undefined,
        layout: widgets,
        kpis: [...new Set(kpis)], // Remove duplicates
        filters: {
          date_range: 'last_30_days',
          vendor: 'all'
        },
        is_default: isDefault,
        is_active: true,
        display_order: 0
      }

      await createDashboard.mutateAsync(dashboardConfig)

      setSaveSuccess(true)

      // Redirect to dashboard after short delay
      setTimeout(() => {
        navigate('/')
      }, 1500)
    } catch (error: any) {
      console.error('Failed to save dashboard:', error)
      setSaveError(error.message || 'Failed to save dashboard. Please try again.')
    }
  }

  // Preview configuration
  const previewConfig: DashboardConfig = {
    dashboard_id: 'preview',
    user_id: null,
    dashboard_name: dashboardName,
    description: description || null,
    layout: widgets,
    kpis: [],
    filters: {
      date_range: 'last_30_days',
      vendor: 'all'
    },
    is_default: isDefault,
    is_active: true,
    display_order: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigate('/')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard Builder</h1>
            <p className="text-muted-foreground">Create your custom dashboard</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setSelectedTab('preview')}
            disabled={widgets.length === 0}
          >
            <Eye className="h-4 w-4 mr-2" />
            Preview
          </Button>
          <Button
            onClick={handleSaveDashboard}
            disabled={createDashboard.isPending || widgets.length === 0}
          >
            <Save className="h-4 w-4 mr-2" />
            {createDashboard.isPending ? 'Saving...' : 'Save Dashboard'}
          </Button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {saveSuccess && (
        <Alert variant="default" className="bg-success/10 border-success">
          <CheckCircle className="h-4 w-4 text-success" />
          <AlertDescription className="text-success">
            Dashboard saved successfully! Redirecting...
          </AlertDescription>
        </Alert>
      )}

      {saveError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{saveError}</AlertDescription>
        </Alert>
      )}

      {/* Dashboard Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Dashboard Settings</CardTitle>
          <CardDescription>Configure basic dashboard properties</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Dashboard Name *</Label>
              <Input
                id="name"
                value={dashboardName}
                onChange={(e) => setDashboardName(e.target.value)}
                placeholder="Enter dashboard name"
              />
            </div>

            <div className="flex items-center justify-between p-4 rounded-lg border">
              <div className="space-y-0.5 flex-1">
                <Label htmlFor="default">Set as Default Dashboard</Label>
                <p className="text-sm text-muted-foreground">
                  This dashboard will load automatically
                </p>
              </div>
              <input
                type="checkbox"
                id="default"
                checked={isDefault}
                onChange={(e) => setIsDefault(e.target.checked)}
                className="h-4 w-4"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this dashboard shows..."
              rows={2}
            />
          </div>
        </CardContent>
      </Card>

      {/* Builder Interface */}
      <div className="space-y-6">
        {/* Tab Navigation */}
        <div className="flex gap-2 border-b">
          <button
            onClick={() => setSelectedTab('build')}
            className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
              selectedTab === 'build'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Layers className="h-4 w-4" />
            Build
          </button>
          <button
            onClick={() => setSelectedTab('preview')}
            disabled={widgets.length === 0}
            className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
              selectedTab === 'preview'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            } ${widgets.length === 0 ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <Eye className="h-4 w-4" />
            Preview
          </button>
        </div>

        {/* Build Tab */}
        {selectedTab === 'build' && (
          <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Widget Gallery / Config Form */}
            <div className="lg:col-span-2">
              {showWidgetGallery && !editingWidget && (
                <WidgetGallery onSelectWidget={handleSelectWidget} />
              )}

              {editingWidget && (
                <WidgetConfigForm
                  widgetType={editingWidget.type}
                  initialConfig={editingWidget}
                  onSave={handleSaveWidget}
                  onCancel={() => {
                    setEditingWidget(null)
                    setShowWidgetGallery(true)
                  }}
                />
              )}
            </div>

            {/* Current Widgets */}
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Dashboard Widgets</CardTitle>
                  <CardDescription>
                    {widgets.length} {widgets.length === 1 ? 'widget' : 'widgets'} added
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {widgets.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground text-sm">
                      <Plus className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>No widgets added yet.</p>
                      <p>Select widgets from the gallery to get started.</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {widgets.map((widget, index) => (
                        <div
                          key={widget.id}
                          className="flex items-center gap-2 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                        >
                          <div className="flex flex-col gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6"
                              onClick={() => handleMoveWidget(widget.id, 'up')}
                              disabled={index === 0}
                            >
                              ▲
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6"
                              onClick={() => handleMoveWidget(widget.id, 'down')}
                              disabled={index === widgets.length - 1}
                            >
                              ▼
                            </Button>
                          </div>

                          <GripVertical className="h-4 w-4 text-muted-foreground" />

                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm truncate">{widget.props.title || widget.type}</p>
                            <p className="text-xs text-muted-foreground">{widget.type}</p>
                          </div>

                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleEditWidget(widget)}
                            >
                              ✏️
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-destructive hover:text-destructive"
                              onClick={() => handleDeleteWidget(widget.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
        )}

        {/* Preview Tab */}
        {selectedTab === 'preview' && (
          <div>
          <Card>
            <CardHeader>
              <CardTitle>Dashboard Preview</CardTitle>
              <CardDescription>
                This is how your dashboard will look (using live data)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DynamicDashboard config={previewConfig} />
            </CardContent>
          </Card>
        </div>
        )}
      </div>
    </div>
  )
}
