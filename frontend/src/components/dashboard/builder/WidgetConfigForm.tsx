/**
 * Widget Configuration Form
 *
 * Visual form for configuring widget options
 * Dynamically renders form fields based on widget configuration schema
 */

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { AlertCircle, Save, X } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import type { WidgetConfigFormState } from '@/types/widgetBuilder'
import type { WidgetConfig } from '@/types/dashboardConfig'
import { getWidgetMetadata } from '@/lib/widgetRegistry'

interface WidgetConfigFormProps {
  widgetType: string
  initialConfig?: WidgetConfig
  onSave: (config: WidgetConfig) => void
  onCancel: () => void
}

export function WidgetConfigForm({
  widgetType,
  initialConfig,
  onSave,
  onCancel
}: WidgetConfigFormProps) {
  const metadata = getWidgetMetadata(widgetType as any)

  // Form state
  const [formState, setFormState] = useState<WidgetConfigFormState>({
    widgetType: widgetType as any,
    title: initialConfig?.props.title || metadata.name,
    dateRange: 'last_30_days',
    showTotal: true,
    showTrend: true,
    showLegend: true,
    showLabels: false,
    limit: 10,
    sortBy: 'revenue',
    chartType: 'line',
    groupBy: 'month',
    colorScheme: 'default'
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const updateField = (field: keyof WidgetConfigFormState, value: any) => {
    setFormState(prev => ({ ...prev, [field]: value }))
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    // Validate required fields based on schema
    if (metadata.configSchema.dataSource?.required) {
      if (!formState.dataSource) {
        newErrors.dataSource = 'Please select at least one data source'
      }
    }

    if (!formState.title || formState.title.trim() === '') {
      newErrors.title = 'Widget title is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSave = () => {
    if (!validateForm()) {
      return
    }

    // Build widget configuration from form state
    // ALL configuration goes in 'props' field per backend schema
    const config: WidgetConfig = {
      id: initialConfig?.id || crypto.randomUUID(),
      type: formState.widgetType,
      position: initialConfig?.position || { row: 0, col: 0, width: 12, height: 4 },
      props: {
        title: formState.title || metadata.name,
        dateRange: formState.dateRange,
        showTotal: formState.showTotal,
        showTrend: formState.showTrend,
        chartType: formState.chartType,
        groupBy: formState.groupBy,
        sortBy: formState.sortBy,
        limit: formState.limit,
        colorScheme: formState.colorScheme,
        showLegend: formState.showLegend,
        showLabels: formState.showLabels,
        ...(formState.dataSource && { dataSource: formState.dataSource })
      }
    }

    onSave(config)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{metadata.name} Configuration</CardTitle>
        <CardDescription>{metadata.description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Widget Title */}
        <div className="space-y-2">
          <Label htmlFor="title">Widget Title</Label>
          <Input
            id="title"
            value={formState.title}
            onChange={(e) => updateField('title', e.target.value)}
            placeholder="Enter widget title"
          />
          {errors.title && (
            <p className="text-sm text-destructive">{errors.title}</p>
          )}
        </div>

        {/* Data Source Selection (if applicable) */}
        {metadata.configSchema.dataSource && (
          <div className="space-y-2">
            <Label>Data Source</Label>
            <p className="text-sm text-muted-foreground">
              {metadata.configSchema.dataSource.type === 'multiselect'
                ? 'Select one or more metrics to display'
                : 'Select the data source for this widget'}
            </p>

            {metadata.configSchema.dataSource.options.map(option => (
              <div key={option.value} className="flex items-center space-x-2 p-3 rounded-lg border">
                <input
                  type={metadata.configSchema.dataSource?.type === 'multiselect' ? 'checkbox' : 'radio'}
                  id={option.value}
                  name="dataSource"
                  checked={
                    metadata.configSchema.dataSource?.type === 'multiselect'
                      ? (formState.dataSource as string[] || []).includes(option.value)
                      : formState.dataSource === option.value
                  }
                  onChange={(e) => {
                    if (metadata.configSchema.dataSource?.type === 'multiselect') {
                      const current = (formState.dataSource as string[]) || []
                      const updated = e.target.checked
                        ? [...current, option.value]
                        : current.filter(v => v !== option.value)
                      updateField('dataSource', updated)
                    } else {
                      updateField('dataSource', option.value)
                    }
                  }}
                  className="h-4 w-4"
                />
                <div className="flex-1">
                  <Label htmlFor={option.value} className="font-medium cursor-pointer">
                    {option.label}
                  </Label>
                  {option.description && (
                    <p className="text-sm text-muted-foreground">{option.description}</p>
                  )}
                </div>
              </div>
            ))}
            {errors.dataSource && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{errors.dataSource}</AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {/* Display Options */}
        {metadata.configSchema.displayOptions && (
          <div className="space-y-4">
            <h3 className="font-medium">Display Options</h3>

            {/* Chart Type */}
            {metadata.configSchema.displayOptions.chartType && (
              <div className="space-y-2">
                <Label htmlFor="chartType">
                  {metadata.configSchema.displayOptions.chartType.label}
                </Label>
                <Select
                  options={metadata.configSchema.displayOptions.chartType.options}
                  value={formState.chartType}
                  onValueChange={(value) => updateField('chartType', value)}
                  placeholder="Select chart type"
                />
                {metadata.configSchema.displayOptions.chartType.helpText && (
                  <p className="text-sm text-muted-foreground">
                    {metadata.configSchema.displayOptions.chartType.helpText}
                  </p>
                )}
              </div>
            )}

            {/* Group By */}
            {metadata.configSchema.displayOptions.groupBy && (
              <div className="space-y-2">
                <Label htmlFor="groupBy">
                  {metadata.configSchema.displayOptions.groupBy.label}
                </Label>
                <Select
                  options={metadata.configSchema.displayOptions.groupBy.options}
                  value={formState.groupBy}
                  onValueChange={(value) => updateField('groupBy', value)}
                  placeholder="Select grouping"
                />
              </div>
            )}

            {/* Sort By */}
            {metadata.configSchema.displayOptions.sortBy && (
              <div className="space-y-2">
                <Label htmlFor="sortBy">
                  {metadata.configSchema.displayOptions.sortBy.label}
                </Label>
                <Select
                  options={metadata.configSchema.displayOptions.sortBy.options}
                  value={formState.sortBy}
                  onValueChange={(value) => updateField('sortBy', value)}
                  placeholder="Select sorting"
                />
                {metadata.configSchema.displayOptions.sortBy.helpText && (
                  <p className="text-sm text-muted-foreground">
                    {metadata.configSchema.displayOptions.sortBy.helpText}
                  </p>
                )}
              </div>
            )}

            {/* Limit */}
            {metadata.configSchema.displayOptions.limit && (
              <div className="space-y-2">
                <Label htmlFor="limit">
                  {metadata.configSchema.displayOptions.limit.label}
                </Label>
                <Input
                  id="limit"
                  type="number"
                  min={metadata.configSchema.displayOptions.limit.min}
                  max={metadata.configSchema.displayOptions.limit.max}
                  value={formState.limit}
                  onChange={(e) => updateField('limit', parseInt(e.target.value) || 10)}
                />
                {metadata.configSchema.displayOptions.limit.helpText && (
                  <p className="text-sm text-muted-foreground">
                    {metadata.configSchema.displayOptions.limit.helpText}
                  </p>
                )}
              </div>
            )}

            {/* Boolean Toggles */}
            {metadata.configSchema.displayOptions.showTotal && (
              <div className="flex items-center justify-between p-3 rounded-lg border">
                <div className="space-y-0.5 flex-1">
                  <Label htmlFor="showTotal">
                    {metadata.configSchema.displayOptions.showTotal.label}
                  </Label>
                  {metadata.configSchema.displayOptions.showTotal.helpText && (
                    <p className="text-sm text-muted-foreground">
                      {metadata.configSchema.displayOptions.showTotal.helpText}
                    </p>
                  )}
                </div>
                <input
                  type="checkbox"
                  id="showTotal"
                  checked={formState.showTotal}
                  onChange={(e) => updateField('showTotal', e.target.checked)}
                  className="h-4 w-4"
                />
              </div>
            )}

            {metadata.configSchema.displayOptions.showTrend && (
              <div className="flex items-center justify-between p-3 rounded-lg border">
                <div className="space-y-0.5 flex-1">
                  <Label htmlFor="showTrend">
                    {metadata.configSchema.displayOptions.showTrend.label}
                  </Label>
                  {metadata.configSchema.displayOptions.showTrend.helpText && (
                    <p className="text-sm text-muted-foreground">
                      {metadata.configSchema.displayOptions.showTrend.helpText}
                    </p>
                  )}
                </div>
                <input
                  type="checkbox"
                  id="showTrend"
                  checked={formState.showTrend}
                  onChange={(e) => updateField('showTrend', e.target.checked)}
                  className="h-4 w-4"
                />
              </div>
            )}
          </div>
        )}

        {/* Filter Options */}
        {metadata.configSchema.filterOptions?.dateRange && (
          <div className="space-y-4">
            <h3 className="font-medium">Filters</h3>

            <div className="space-y-2">
              <Label htmlFor="dateRange">
                {metadata.configSchema.filterOptions.dateRange.label}
              </Label>
              <Select
                options={metadata.configSchema.filterOptions.dateRange.presets}
                value={formState.dateRange}
                onValueChange={(value) => updateField('dateRange', value)}
                placeholder="Select date range"
              />
            </div>
          </div>
        )}

        {/* Visual Options */}
        {metadata.configSchema.visualOptions && (
          <div className="space-y-4">
            <h3 className="font-medium">Visual Settings</h3>

            {metadata.configSchema.visualOptions.showLegend && (
              <div className="flex items-center justify-between p-3 rounded-lg border">
                <div className="space-y-0.5 flex-1">
                  <Label htmlFor="showLegend">
                    {metadata.configSchema.visualOptions.showLegend.label}
                  </Label>
                </div>
                <input
                  type="checkbox"
                  id="showLegend"
                  checked={formState.showLegend}
                  onChange={(e) => updateField('showLegend', e.target.checked)}
                  className="h-4 w-4"
                />
              </div>
            )}

            {metadata.configSchema.visualOptions.showLabels && (
              <div className="flex items-center justify-between p-3 rounded-lg border">
                <div className="space-y-0.5 flex-1">
                  <Label htmlFor="showLabels">
                    {metadata.configSchema.visualOptions.showLabels.label}
                  </Label>
                </div>
                <input
                  type="checkbox"
                  id="showLabels"
                  checked={formState.showLabels}
                  onChange={(e) => updateField('showLabels', e.target.checked)}
                  className="h-4 w-4"
                />
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4">
          <Button onClick={handleSave} className="flex-1">
            <Save className="h-4 w-4 mr-2" />
            Save Widget
          </Button>
          <Button onClick={onCancel} variant="outline">
            <X className="h-4 w-4 mr-2" />
            Cancel
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
