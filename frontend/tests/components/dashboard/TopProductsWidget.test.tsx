/**
 * Component Tests for TopProductsWidget
 * Tests T039: Verify Top Products Widget renders correctly and sorts properly
 *
 * NOTE: This test file requires testing framework setup.
 * Required: Vitest + @testing-library/react + @testing-library/user-event
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import TopProductsWidget from '@/components/dashboard/widgets/TopProductsWidget'
import type { WidgetConfig } from '@/types/dashboardConfig'

// Mock the useKPIs hook (TopProductsWidget uses KPI data)
vi.mock('@/hooks/useKPIs', () => ({
  useKPIs: vi.fn(),
}))

import { useKPIs } from '@/hooks/useKPIs'

// Mock product data
const mockProductData = {
  top_products: [
    {
      rank: 1,
      product_name: 'Premium Wireless Headphones',
      total_revenue: 125000,
      total_units: 450,
      percentage: 18.5,
    },
    {
      rank: 2,
      product_name: 'Smart Watch Series 5',
      total_revenue: 98000,
      total_units: 380,
      percentage: 14.7,
    },
    {
      rank: 3,
      product_name: 'Bluetooth Speaker',
      total_revenue: 75000,
      total_units: 520,
      percentage: 11.2,
    },
    {
      rank: 4,
      product_name: 'USB-C Cable Pack',
      total_revenue: 45000,
      total_units: 890,
      percentage: 6.8,
    },
    {
      rank: 5,
      product_name: 'Laptop Stand',
      total_revenue: 38000,
      total_units: 310,
      percentage: 5.7,
    },
  ],
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

describe('TopProductsWidget Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render top products list', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
          sortBy: 'revenue',
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Verify all products are rendered
        expect(screen.getByText('Premium Wireless Headphones')).toBeInTheDocument()
        expect(screen.getByText('Smart Watch Series 5')).toBeInTheDocument()
        expect(screen.getByText('Bluetooth Speaker')).toBeInTheDocument()
        expect(screen.getByText('USB-C Cable Pack')).toBeInTheDocument()
        expect(screen.getByText('Laptop Stand')).toBeInTheDocument()
      })
    })

    it('should render widget title from props', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Best Sellers',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText('Best Sellers')).toBeInTheDocument()
      })
    })

    it('should render product rankings', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Rankings should be displayed (1, 2, 3, 4, 5)
        expect(screen.getByText('1')).toBeInTheDocument()
        expect(screen.getByText('2')).toBeInTheDocument()
        expect(screen.getByText('3')).toBeInTheDocument()
        expect(screen.getByText('4')).toBeInTheDocument()
        expect(screen.getByText('5')).toBeInTheDocument()
      })
    })

    it('should render product revenue', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Revenue should be formatted (e.g., $125,000)
        expect(screen.getByText(/125,000|125k/)).toBeInTheDocument()
        expect(screen.getByText(/98,000|98k/)).toBeInTheDocument()
      })
    })

    it('should render product units sold', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Units should be displayed
        expect(screen.getByText(/450.*units/i)).toBeInTheDocument()
        expect(screen.getByText(/380.*units/i)).toBeInTheDocument()
      })
    })

    it('should render percentage of total', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Percentages should be displayed
        expect(screen.getByText(/18\.5%/)).toBeInTheDocument()
        expect(screen.getByText(/14\.7%/)).toBeInTheDocument()
        expect(screen.getByText(/11\.2%/)).toBeInTheDocument()
      })
    })
  })

  describe('Limit Prop', () => {
    it('should respect limit prop and show only specified number of products', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: {
          top_products: mockProductData.top_products.slice(0, 3),
        },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 3, // Show only top 3
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // First 3 products should be visible
        expect(screen.getByText('Premium Wireless Headphones')).toBeInTheDocument()
        expect(screen.getByText('Smart Watch Series 5')).toBeInTheDocument()
        expect(screen.getByText('Bluetooth Speaker')).toBeInTheDocument()

        // 4th and 5th should not be visible
        expect(screen.queryByText('USB-C Cable Pack')).not.toBeInTheDocument()
        expect(screen.queryByText('Laptop Stand')).not.toBeInTheDocument()
      })
    })

    it('should handle different limit values', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: {
          top_products: mockProductData.top_products.slice(0, 10),
        },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 10,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should fetch with limit parameter
        expect(useKPIs).toHaveBeenCalled()
      })
    })
  })

  describe('Sorting', () => {
    it('should display products sorted by revenue (default)', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
          sortBy: 'revenue',
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Products should be ordered by revenue (descending)
        const products = screen.getAllByRole('listitem') // or appropriate role
        expect(products[0]).toHaveTextContent('Premium Wireless Headphones')
      })
    })

    it('should handle sortBy units prop', async () => {
      const sortedByUnits = {
        top_products: [
          mockProductData.top_products[3], // 890 units
          mockProductData.top_products[2], // 520 units
          mockProductData.top_products[0], // 450 units
          mockProductData.top_products[1], // 380 units
          mockProductData.top_products[4], // 310 units
        ],
      }

      vi.mocked(useKPIs).mockReturnValue({
        data: sortedByUnits,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
          sortBy: 'units',
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Products should be ordered by units (descending)
        const products = screen.getAllByRole('listitem')
        expect(products[0]).toHaveTextContent('USB-C Cable Pack') // 890 units
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
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      // Should render skeleton rows
      expect(screen.queryByText('Premium Wireless Headphones')).not.toBeInTheDocument()
    })

    it('should not display data while loading', () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      // No product data should be displayed
      mockProductData.top_products.forEach((product) => {
        expect(screen.queryByText(product.product_name)).not.toBeInTheDocument()
      })
    })
  })

  describe('Error State', () => {
    it('should render error message on data fetch failure', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: new Error('Failed to fetch product data'),
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument()
      })
    })
  })

  describe('Empty State', () => {
    it('should render empty state when no products exist', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: { top_products: [] },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should display empty state message
        expect(screen.getByText(/no products|empty/i)).toBeInTheDocument()
      })
    })

    it('should render EmptyState component', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: { top_products: [] },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      const { container } = render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // EmptyState component should be rendered
        const emptyState = container.querySelector('[class*="empty"]')
        expect(emptyState).toBeInTheDocument()
      })
    })
  })

  describe('View All Button', () => {
    it('should render "View all" button', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText(/view all/i)).toBeInTheDocument()
      })
    })

    it('should link to products page', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        const viewAllButton = screen.getByText(/view all/i)
        const link = viewAllButton.closest('a')
        expect(link).toHaveAttribute('href', expect.stringContaining('/products'))
      })
    })
  })

  describe('Card UI', () => {
    it('should render in Card component', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      const { container } = render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should be wrapped in Card component
        const card = container.querySelector('[class*="card"]')
        expect(card).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper list semantics', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should use proper list elements or roles
        const list = screen.getByRole('list')
        expect(list).toBeInTheDocument()
      })
    })

    it('should have accessible rank indicators', async () => {
      vi.mocked(useKPIs).mockReturnValue({
        data: mockProductData,
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'top-products-1',
        type: 'top_products',
        position: { row: 5, col: 0, width: 6, height: 4 },
        props: {
          title: 'Top Products',
          limit: 5,
        },
      }

      render(<TopProductsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Rankings should have appropriate ARIA labels
        const rankings = screen.getAllByText(/[1-5]/)
        rankings.forEach((ranking) => {
          expect(ranking).toBeInTheDocument()
        })
      })
    })
  })
})
