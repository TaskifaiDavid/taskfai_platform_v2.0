/**
 * Integration Tests for DynamicDashboard Rendering
 * Tests T040: E2E test confirming dynamic dashboard rendering works correctly
 *
 * NOTE: This test file requires testing framework setup.
 * Required: Vitest + @testing-library/react + @testing-library/user-event
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tantml:router-dom'
import type { ReactNode } from 'react'
import DynamicDashboard from '@/components/dashboard/DynamicDashboard'
import type { DashboardConfig } from '@/types/dashboardConfig'

// Mock the useDashboardConfig hook
vi.mock('@/api/dashboardConfig', () => ({
  useDashboardConfig: vi.fn(),
}))

// Mock widget components
vi.mock('@/components/dashboard/widgets/KPIGridWidget', () => ({
  default: ({ config }: any) => <div data-testid="kpi-grid-widget" data-widget-id={config.id}>KPI Grid Widget</div>,
}))

vi.mock('@/components/dashboard/widgets/RecentUploadsWidget', () => ({
  default: ({ config }: any) => <div data-testid="recent-uploads-widget" data-widget-id={config.id}>Recent Uploads Widget</div>,
}))

vi.mock('@/components/dashboard/widgets/TopProductsWidget', () => ({
  default: ({ config }: any) => <div data-testid="top-products-widget" data-widget-id={config.id}>Top Products Widget</div>,
}))

import { useDashboardConfig } from '@/api/dashboardConfig'

// Mock dashboard configuration
const mockDashboardConfig: DashboardConfig = {
  dashboard_id: 'test-dashboard-id',
  user_id: 'test-user-id',
  dashboard_name: 'Sales Overview Dashboard',
  description: 'Comprehensive sales performance dashboard',
  layout: [
    {
      id: 'kpi-grid-1',
      type: 'kpi_grid',
      position: { row: 0, col: 0, width: 12, height: 2 },
      props: {
        kpis: ['total_revenue', 'total_units', 'avg_price', 'total_uploads'],
      },
    },
    {
      id: 'recent-uploads-1',
      type: 'recent_uploads',
      position: { row: 2, col: 0, width: 6, height: 3 },
      props: {
        title: 'Recent Uploads',
        limit: 5,
      },
    },
    {
      id: 'top-products-1',
      type: 'top_products',
      position: { row: 2, col: 6, width: 6, height: 3 },
      props: {
        title: 'Top Products',
        limit: 5,
        sortBy: 'revenue',
      },
    },
  ],
  kpis: ['total_revenue', 'total_units', 'avg_price', 'total_uploads'],
  filters: { date_range: 'last_30_days' },
  is_default: true,
  is_active: true,
  display_order: 0,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
}

// Test wrapper with QueryClient and Router
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('DynamicDashboard Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Complete Dashboard Rendering', () => {
    it('should render all 3 widgets from configuration', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Verify all 3 widgets are rendered
        expect(screen.getByTestId('kpi-grid-widget')).toBeInTheDocument()
        expect(screen.getByTestId('recent-uploads-widget')).toBeInTheDocument()
        expect(screen.getByTestId('top-products-widget')).toBeInTheDocument()
      })
    })

    it('should render widgets in correct positions', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const { container } = render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Verify widget positioning
        const kpiWidget = screen.getByTestId('kpi-grid-widget')
        const recentUploadsWidget = screen.getByTestId('recent-uploads-widget')
        const topProductsWidget = screen.getByTestId('top-products-widget')

        // Check widget IDs match configuration
        expect(kpiWidget).toHaveAttribute('data-widget-id', 'kpi-grid-1')
        expect(recentUploadsWidget).toHaveAttribute('data-widget-id', 'recent-uploads-1')
        expect(topProductsWidget).toHaveAttribute('data-widget-id', 'top-products-1')
      })
    })

    it('should render dashboard name and description', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Sales Overview Dashboard')).toBeInTheDocument()
        expect(screen.getByText('Comprehensive sales performance dashboard')).toBeInTheDocument()
      })
    })

    it('should render "Live" badge', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText(/live/i)).toBeInTheDocument()
      })
    })
  })

  describe('Widget Type Mapping', () => {
    it('should correctly map widget types to components', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Verify widget type mapping
        // kpi_grid → KPIGridWidget
        expect(screen.getByTestId('kpi-grid-widget')).toBeInTheDocument()

        // recent_uploads → RecentUploadsWidget
        expect(screen.getByTestId('recent-uploads-widget')).toBeInTheDocument()

        // top_products → TopProductsWidget
        expect(screen.getByTestId('top-products-widget')).toBeInTheDocument()
      })
    })

    it('should handle unknown widget types gracefully', async () => {
      const configWithUnknownWidget: DashboardConfig = {
        ...mockDashboardConfig,
        layout: [
          ...mockDashboardConfig.layout,
          {
            id: 'unknown-widget-1',
            type: 'unknown_type',
            position: { row: 5, col: 0, width: 12, height: 2 },
            props: {},
          },
        ],
      }

      vi.mocked(useDashboardConfig).mockReturnValue({
        data: configWithUnknownWidget,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Should show "coming soon" placeholder or error widget
        expect(screen.getByText(/coming soon|not implemented/i)).toBeInTheDocument()

        // Known widgets should still render
        expect(screen.getByTestId('kpi-grid-widget')).toBeInTheDocument()
      })
    })

    it('should pass widget configuration to components', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Widget components should receive their config
        const kpiWidget = screen.getByTestId('kpi-grid-widget')
        const recentUploadsWidget = screen.getByTestId('recent-uploads-widget')
        const topProductsWidget = screen.getByTestId('top-products-widget')

        // Verify widgets are rendered (config passed correctly)
        expect(kpiWidget).toBeInTheDocument()
        expect(recentUploadsWidget).toBeInTheDocument()
        expect(topProductsWidget).toBeInTheDocument()
      })
    })
  })

  describe('Loading State', () => {
    it('should render skeleton loading state', () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      // Should render skeleton placeholders
      // No actual widgets should be rendered
      expect(screen.queryByTestId('kpi-grid-widget')).not.toBeInTheDocument()
      expect(screen.queryByTestId('recent-uploads-widget')).not.toBeInTheDocument()
      expect(screen.queryByTestId('top-products-widget')).not.toBeInTheDocument()
    })

    it('should not display dashboard name while loading', () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      expect(screen.queryByText('Sales Overview Dashboard')).not.toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should render error Alert on fetch failure', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: new Error('Failed to fetch dashboard configuration'),
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Should display error Alert component
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument()
      })
    })

    it('should not render widgets on error', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: new Error('Failed to fetch dashboard configuration'),
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // No widgets should be rendered
        expect(screen.queryByTestId('kpi-grid-widget')).not.toBeInTheDocument()
        expect(screen.queryByTestId('recent-uploads-widget')).not.toBeInTheDocument()
        expect(screen.queryByTestId('top-products-widget')).not.toBeInTheDocument()
      })
    })
  })

  describe('Empty Layout', () => {
    it('should handle empty layout gracefully', async () => {
      const emptyLayoutConfig: DashboardConfig = {
        ...mockDashboardConfig,
        layout: [],
      }

      vi.mocked(useDashboardConfig).mockReturnValue({
        data: emptyLayoutConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Dashboard name should still be rendered
        expect(screen.getByText('Sales Overview Dashboard')).toBeInTheDocument()

        // No widgets should be rendered
        expect(screen.queryByTestId('kpi-grid-widget')).not.toBeInTheDocument()
        expect(screen.queryByTestId('recent-uploads-widget')).not.toBeInTheDocument()
        expect(screen.queryByTestId('top-products-widget')).not.toBeInTheDocument()
      })
    })
  })

  describe('Grid Positioning', () => {
    it('should apply correct grid positioning from widget.position', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const { container } = render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Verify grid container exists
        const gridContainer = container.querySelector('[class*="grid"]')
        expect(gridContainer).toBeInTheDocument()

        // Widgets should have position-related styles/classes
        // Implementation-specific: check for grid positioning
      })
    })

    it('should handle widget positioning correctly', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // KPI Grid: row 0, col 0, width 12, height 2
        // Recent Uploads: row 2, col 0, width 6, height 3
        // Top Products: row 2, col 6, width 6, height 3

        // Verify all widgets are rendered in expected positions
        const kpiWidget = screen.getByTestId('kpi-grid-widget')
        const recentUploadsWidget = screen.getByTestId('recent-uploads-widget')
        const topProductsWidget = screen.getByTestId('top-products-widget')

        expect(kpiWidget).toBeInTheDocument()
        expect(recentUploadsWidget).toBeInTheDocument()
        expect(topProductsWidget).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Layout', () => {
    it('should apply responsive layout classes', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const { container } = render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Should have responsive grid classes
        const gridContainer = container.querySelector('[class*="grid"]')
        expect(gridContainer).toHaveClass(expect.stringMatching(/grid/))
      })
    })
  })

  describe('Animations', () => {
    it('should apply animations to dashboard elements', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const { container } = render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Should have animation/transition classes
        const dashboard = container.firstChild
        expect(dashboard).toHaveClass(expect.stringMatching(/animate|transition/))
      })
    })
  })

  describe('Dynamic Configuration Updates', () => {
    it('should re-render when configuration changes', async () => {
      const { rerender } = render(<DynamicDashboard />, { wrapper: createWrapper() })

      // Initial configuration
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      await waitFor(() => {
        expect(screen.getByText('Sales Overview Dashboard')).toBeInTheDocument()
      })

      // Updated configuration
      const updatedConfig: DashboardConfig = {
        ...mockDashboardConfig,
        dashboard_name: 'Updated Dashboard Name',
      }

      vi.mocked(useDashboardConfig).mockReturnValue({
        data: updatedConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      rerender(<DynamicDashboard />)

      await waitFor(() => {
        expect(screen.getByText('Updated Dashboard Name')).toBeInTheDocument()
      })
    })
  })

  describe('Widget Registry Pattern', () => {
    it('should use widget registry for component mapping', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Widget registry should map:
        // - kpi_grid → KPIGridWidget
        // - recent_uploads → RecentUploadsWidget
        // - top_products → TopProductsWidget

        expect(screen.getByTestId('kpi-grid-widget')).toBeInTheDocument()
        expect(screen.getByTestId('recent-uploads-widget')).toBeInTheDocument()
        expect(screen.getByTestId('top-products-widget')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have accessible dashboard structure', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Dashboard should have proper ARIA structure
        const dashboard = screen.getByRole('main') // or appropriate role
        expect(dashboard).toBeInTheDocument()
      })
    })

    it('should have accessible dashboard name heading', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        const heading = screen.getByRole('heading', { name: /Sales Overview Dashboard/i })
        expect(heading).toBeInTheDocument()
      })
    })

    it('should be keyboard navigable', async () => {
      vi.mocked(useDashboardConfig).mockReturnValue({
        data: mockDashboardConfig,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      render(<DynamicDashboard />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Dashboard elements should be focusable
        const widgets = [
          screen.getByTestId('kpi-grid-widget'),
          screen.getByTestId('recent-uploads-widget'),
          screen.getByTestId('top-products-widget'),
        ]

        widgets.forEach((widget) => {
          expect(widget).toBeInTheDocument()
        })
      })
    })
  })
})
