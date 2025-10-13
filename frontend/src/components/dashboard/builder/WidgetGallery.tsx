/**
 * Widget Gallery Component
 *
 * Displays all available widgets in a visual gallery
 * Users can browse and select widgets to add to their dashboard
 */

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  BarChart3,
  TrendingUp,
  LineChart,
  Package,
  Users,
  PieChart,
  FileUp,
  Plus,
  Search
} from 'lucide-react'
import { getAllWidgets } from '@/lib/widgetRegistry'
import type { WidgetMetadata } from '@/types/widgetBuilder'
import { cn } from '@/lib/utils'

interface WidgetGalleryProps {
  onSelectWidget: (widget: WidgetMetadata) => void
  className?: string
}

// Icon mapping for Lucide icons
const ICON_MAP: Record<string, typeof BarChart3> = {
  BarChart3,
  TrendingUp,
  LineChart,
  Package,
  Users,
  PieChart,
  FileUp
}

// Category display names
const CATEGORY_NAMES = {
  metrics: 'Metrics & KPIs',
  charts: 'Charts & Graphs',
  tables: 'Tables & Lists',
  lists: 'Activity Feeds'
}

export function WidgetGallery({ onSelectWidget, className }: WidgetGalleryProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | 'all'>('all')

  const allWidgets = getAllWidgets()

  // Filter widgets based on search and category
  const filteredWidgets = allWidgets.filter(widget => {
    const matchesSearch = !searchQuery ||
      widget.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      widget.description.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesCategory = selectedCategory === 'all' || widget.category === selectedCategory

    return matchesSearch && matchesCategory
  })

  const handleWidgetClick = (widget: WidgetMetadata) => {
    onSelectWidget(widget)
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Widget Gallery</h2>
          <p className="text-muted-foreground">
            Choose widgets to add to your dashboard
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search widgets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2">
          <Badge
            variant={selectedCategory === 'all' ? 'default' : 'outline'}
            className="cursor-pointer"
            onClick={() => setSelectedCategory('all')}
          >
            All Widgets
          </Badge>
          {Object.entries(CATEGORY_NAMES).map(([key, label]) => (
            <Badge
              key={key}
              variant={selectedCategory === key ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setSelectedCategory(key)}
            >
              {label}
            </Badge>
          ))}
        </div>
      </div>

      {/* Widget Grid */}
      {filteredWidgets.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No widgets found matching your search.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredWidgets.map((widget) => {
            const IconComponent = ICON_MAP[widget.icon] || BarChart3

            return (
              <Card
                key={widget.type}
                className="group cursor-pointer transition-all hover:shadow-lg hover:scale-105 border-2 hover:border-primary"
                onClick={() => handleWidgetClick(widget)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                        <IconComponent className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{widget.name}</CardTitle>
                        <Badge variant="secondary" className="mt-1 text-xs">
                          {CATEGORY_NAMES[widget.category]}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <CardDescription className="text-sm leading-relaxed">
                    {widget.description}
                  </CardDescription>

                  <Button
                    size="sm"
                    className="w-full"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleWidgetClick(widget)
                    }}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Widget
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Widget Count */}
      <div className="text-sm text-muted-foreground text-center">
        Showing {filteredWidgets.length} of {allWidgets.length} widgets
      </div>
    </div>
  )
}
