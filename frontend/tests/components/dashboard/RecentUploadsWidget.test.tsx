/**
 * Component Tests for RecentUploadsWidget
 * Tests T038: Verify Recent Uploads Widget renders correctly and respects limit prop
 *
 * NOTE: This test file requires testing framework setup.
 * Required: Vitest + @testing-library/react + @testing-library/user-event
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import RecentUploadsWidget from '@/components/dashboard/widgets/RecentUploadsWidget'
import type { WidgetConfig } from '@/types/dashboardConfig'

// Mock the useUploadsList hook
vi.mock('@/api/uploads', () => ({
  useUploadsList: vi.fn(),
}))

import { useUploadsList } from '@/api/uploads'

// Mock upload data
const mockUploads = [
  {
    id: '1',
    filename: 'sales_data_january.xlsx',
    status: 'completed',
    upload_timestamp: '2025-01-15T10:30:00Z',
    vendor_name: 'BoxNox',
    total_rows: 1250,
  },
  {
    id: '2',
    filename: 'inventory_update.csv',
    status: 'completed',
    upload_timestamp: '2025-01-15T09:15:00Z',
    vendor_name: 'Galilu',
    total_rows: 850,
  },
  {
    id: '3',
    filename: 'customer_orders.xlsx',
    status: 'processing',
    upload_timestamp: '2025-01-15T08:00:00Z',
    vendor_name: 'Skins SA',
    total_rows: null,
  },
  {
    id: '4',
    filename: 'product_catalog.csv',
    status: 'failed',
    upload_timestamp: '2025-01-14T16:45:00Z',
    vendor_name: 'BoxNox',
    total_rows: null,
  },
  {
    id: '5',
    filename: 'returns_data.xlsx',
    status: 'completed',
    upload_timestamp: '2025-01-14T15:30:00Z',
    vendor_name: 'Galilu',
    total_rows: 320,
  },
]

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

describe('RecentUploadsWidget Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render recent uploads table', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: mockUploads.slice(0, 3), total: 3 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Verify table headers
        expect(screen.getByText(/filename/i)).toBeInTheDocument()
        expect(screen.getByText(/status/i)).toBeInTheDocument()
        expect(screen.getByText(/timestamp|date/i)).toBeInTheDocument()

        // Verify upload data
        expect(screen.getByText('sales_data_january.xlsx')).toBeInTheDocument()
        expect(screen.getByText('inventory_update.csv')).toBeInTheDocument()
        expect(screen.getByText('customer_orders.xlsx')).toBeInTheDocument()
      })
    })

    it('should render widget title from props', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: mockUploads.slice(0, 3), total: 3 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Latest File Uploads',
          limit: 5,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText('Latest File Uploads')).toBeInTheDocument()
      })
    })

    it('should render all upload columns', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: [mockUploads[0]], total: 1 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        const upload = mockUploads[0]

        // Filename
        expect(screen.getByText(upload.filename)).toBeInTheDocument()

        // Status
        expect(screen.getByText(/completed/i)).toBeInTheDocument()

        // Timestamp (formatted)
        expect(screen.getByText(/2025-01-15|Jan 15|January 15/)).toBeInTheDocument()
      })
    })
  })

  describe('Limit Prop', () => {
    it('should respect limit prop and show only specified number of rows', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: mockUploads.slice(0, 3), total: 5 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 3, // Show only 3 uploads
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should call API with limit parameter
        expect(useUploadsList).toHaveBeenCalledWith(
          expect.objectContaining({ limit: 3 })
        )
      })
    })

    it('should handle different limit values', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: mockUploads, total: 5 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 10,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(useUploadsList).toHaveBeenCalledWith(
          expect.objectContaining({ limit: 10 })
        )
      })
    })

    it('should use default limit when not specified', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: mockUploads.slice(0, 5), total: 5 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          // No limit specified
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should use default limit (e.g., 5)
        expect(useUploadsList).toHaveBeenCalled()
      })
    })
  })

  describe('Status Display', () => {
    it('should display different upload statuses correctly', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: mockUploads.slice(0, 4), total: 4 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Completed status
        expect(screen.getAllByText(/completed/i)).toHaveLength(2)

        // Processing status
        expect(screen.getByText(/processing/i)).toBeInTheDocument()

        // Failed status
        expect(screen.getByText(/failed/i)).toBeInTheDocument()
      })
    })

    it('should apply appropriate status colors/badges', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: [mockUploads[0], mockUploads[3]], total: 2 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      const { container } = render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Status badges should have different colors (success, error, etc.)
        const badges = container.querySelectorAll('[class*="badge"]')
        expect(badges.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Loading State', () => {
    it('should render skeleton loading state', () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      // Should render skeleton rows
      expect(screen.queryByText('sales_data_january.xlsx')).not.toBeInTheDocument()
    })

    it('should not display data while loading', () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      // No actual upload data should be displayed
      mockUploads.forEach((upload) => {
        expect(screen.queryByText(upload.filename)).not.toBeInTheDocument()
      })
    })
  })

  describe('Error State', () => {
    it('should render error message on data fetch failure', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: new Error('Failed to fetch uploads'),
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument()
      })
    })
  })

  describe('Empty State', () => {
    it('should render empty state when no uploads exist', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: [], total: 0 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should display empty state message
        expect(screen.getByText(/no uploads|empty/i)).toBeInTheDocument()
      })
    })

    it('should render EmptyState component', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: [], total: 0 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      const { container } = render(<RecentUploadsWidget config={widgetConfig} />, {
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
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: mockUploads.slice(0, 3), total: 5 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 3,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText(/view all/i)).toBeInTheDocument()
      })
    })

    it('should link to uploads page', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: mockUploads.slice(0, 3), total: 5 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 3,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        const viewAllButton = screen.getByText(/view all/i)
        const link = viewAllButton.closest('a')
        expect(link).toHaveAttribute('href', expect.stringContaining('/uploads'))
      })
    })
  })

  describe('Card UI', () => {
    it('should render in Card component', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: mockUploads.slice(0, 3), total: 3 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      const { container } = render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should be wrapped in Card component
        const card = container.querySelector('[class*="card"]')
        expect(card).toBeInTheDocument()
      })
    })
  })

  describe('Timestamp Formatting', () => {
    it('should format timestamps in human-readable format', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: [mockUploads[0]], total: 1 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should display formatted date (e.g., "Jan 15, 2025" or "2 hours ago")
        // Exact format depends on implementation
        const dateElement = screen.getByText(/2025-01-15|Jan|January/)
        expect(dateElement).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper table semantics', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: mockUploads.slice(0, 3), total: 3 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should use proper table elements or roles
        const table = screen.getByRole('table')
        expect(table).toBeInTheDocument()
      })
    })

    it('should have accessible table headers', async () => {
      vi.mocked(useUploadsList).mockReturnValue({
        data: { uploads: mockUploads.slice(0, 3), total: 3 },
        isLoading: false,
        isError: false,
        error: null,
      } as any)

      const widgetConfig: WidgetConfig = {
        id: 'recent-uploads-1',
        type: 'recent_uploads',
        position: { row: 2, col: 0, width: 12, height: 3 },
        props: {
          title: 'Recent Uploads',
          limit: 5,
        },
      }

      render(<RecentUploadsWidget config={widgetConfig} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        const headers = screen.getAllByRole('columnheader')
        expect(headers.length).toBeGreaterThan(0)
      })
    })
  })
})
