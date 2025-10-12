/**
 * Component Tests for KPIGridWidget
 * Tests T037: Verify KPI Grid Widget renders correctly with various configurations
 *
 * NOTE: This test file requires testing framework setup.
 * Required: Vitest + @testing-library/react + @testing-library/user-event
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import KPIGridWidget from '@/components/dashboard/widgets/KPIGridWidget'
import type { WidgetConfig } from '@/types/dashboardConfig'

// Mock the useKPIs hook
vi.mock('@/hooks/useKPIs', () => ({
  useKPIs: vi.fn(),
}))

import { useKPIs } from '@/hooks/useKPIs'

// Mock KPI data
const mockKPIData = {
  total_revenue: {
    label: 'Total Revenue',
    value: 1250000,
    format: 'currency',
    trend: 12.5,
    sparklineData: [100, 120, 115, 130, 125],
  },
  total_units: {
    label: 'Total Units Sold',
    value: 45000,
    format: 'number',
    trend: 8.3,
    sparklineData: [400, 420, 450, 460, 450],
  },
  avg_price: {
    label: 'Average Price',
    value: 27.78,
    format: 'currency',
    trend: -3.2,
    sparklineData: [28, 29, 28, 27, 27.78],
  },
  total_uploads: {
    label: 'Total Uploads',
    value: 127,
    format: 'number',
    trend: 5.0,
    sparklineData: [100, 110, 115, 120, 127],
  },
}

// Test wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('KPIGridWidget Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render KPI grid with all configured KPIs', async () => {
      // Mock useKPIs to return success data
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue', 'total_units', 'avg_price', 'total_uploads'],
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Verify all 4 KPIs are rendered
        expect(screen.getByText('Total Revenue')).toBeInTheDocument()
        expect(screen.getByText('Total Units Sold')).toBeInTheDocument()
        expect(screen.getByText('Average Price')).toBeInTheDocument()
        expect(screen.getByText('Total Uploads')).toBeInTheDocument()
      })
    })

    it('should render correct number of KPI cards', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue', 'total_units'], // Only 2 KPIs
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText('Total Revenue')).toBeInTheDocument()
        expect(screen.getByText('Total Units Sold')).toBeInTheDocument()
        // Should NOT render the other KPIs
        expect(screen.queryByText('Average Price')).not.toBeInTheDocument()
        expect(screen.queryByText('Total Uploads')).not.toBeInTheDocument()
      })
    })

    it('should display KPI values correctly', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue', 'total_units'],
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Check formatted values are displayed
        // (Assuming component formats currency as $1,250,000)
        expect(screen.getByText(/1,250,000/)).toBeInTheDocument()
        expect(screen.getByText(/45,000/)).toBeInTheDocument()
      })
    })

    it('should display trend indicators', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue', 'avg_price'],
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Positive trend (12.5%)
        expect(screen.getByText(/12\.5%/)).toBeInTheDocument()
        // Negative trend (-3.2%)
        expect(screen.getByText(/3\.2%/)).toBeInTheDocument()
      })
    })
  })

  describe('Loading State', () => {
    it('should render skeleton loading state', () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue', 'total_units'],
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      // Should render skeleton placeholders (implementation-specific)
      // Verify loading state is displayed
      expect(screen.queryByText('Total Revenue')).not.toBeInTheDocument()
    })

    it('should not display data while loading', () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue'],
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      // No KPI data should be displayed
      expect(screen.queryByText(/1,250,000/)).not.toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should render error message on data fetch failure', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: new Error('Failed to fetch KPI data'),
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue'],
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should display error state
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })
  })

  describe('Empty State', () => {
    it('should handle empty KPI array', () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: [], // Empty array
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      // Should handle empty configuration gracefully
      // No KPIs should be rendered
      expect(screen.queryByText('Total Revenue')).not.toBeInTheDocument()
    })

    it('should handle missing KPI data gracefully', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: {},
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue'],
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      // Should handle missing data gracefully (no crash)
    })
  })

  describe('Grid Layout', () => {
    it('should render KPIs in grid layout', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue', 'total_units', 'avg_price', 'total_uploads'],
        },
      }

      const { container } = render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Verify grid container exists (implementation-specific class/style)
        const gridContainer = container.querySelector('[class*="grid"]')
        expect(gridContainer).toBeInTheDocument()
      })
    })

    it('should apply responsive grid layout', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue', 'total_units'],
        },
      }

      const { container } = render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should have responsive grid classes (e.g., grid-cols-1 md:grid-cols-2 lg:grid-cols-4)
        const gridContainer = container.firstChild
        expect(gridContainer).toHaveClass(expect.stringMatching(/grid/))
      })
    })
  })

  describe('Sparklines', () => {
    it('should render sparkline charts for KPIs', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue'],
        },
      }

      const { container } = render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Verify sparkline is rendered (implementation uses recharts or similar)
        // Look for SVG element or chart container
        const sparkline = container.querySelector('svg')
        expect(sparkline).toBeInTheDocument()
      })
    })
  })

  describe('Hover Effects', () => {
    it('should apply hover animations to KPI cards', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue'],
        },
      }

      const { container } = render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // KPI cards should have hover effects (transition/animation classes)
        const card = container.querySelector('[class*="card"]')
        expect(card).toHaveClass(expect.stringMatching(/transition|hover/))
      })
    })
  })

  describe('Configuration Props', () => {
    it('should respect widget configuration from props', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'custom-kpi-grid',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 6, height: 2 },
        props: {
          kpis: ['total_revenue', 'total_units'],
          title: 'Sales Metrics', // Custom title (if supported)
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Verify only configured KPIs are rendered
        expect(screen.getByText('Total Revenue')).toBeInTheDocument()
        expect(screen.getByText('Total Units Sold')).toBeInTheDocument()
        expect(screen.queryByText('Average Price')).not.toBeInTheDocument()
      })
    })

    it('should handle unknown KPI types gracefully', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue', 'unknown_kpi', 'total_units'],
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should render valid KPIs and skip unknown ones
        expect(screen.getByText('Total Revenue')).toBeInTheDocument()
        expect(screen.getByText('Total Units Sold')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels for KPI cards', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue'],
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // KPI cards should have accessible labels
        const kpiCard = screen.getByText('Total Revenue').closest('[role]')
        expect(kpiCard).toBeInTheDocument()
      })
    })

    it('should be keyboard navigable', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockKPIData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'kpi-grid-1',
        type: 'kpi_grid',
        position: { row: 0, col: 0, width: 12, height: 2 },
        props: {
          kpis: ['total_revenue', 'total_units'],
        },
      }

      render(<KPIGridWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // KPI cards should be focusable for keyboard navigation
        const cards = screen.getAllByRole('article') // or appropriate role
        cards.forEach((card) => {
          expect(card).toHaveAttribute('tabIndex')
        })
      })
    })
  })
})
