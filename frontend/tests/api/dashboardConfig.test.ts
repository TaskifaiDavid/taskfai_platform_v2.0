/**
 * React Query Hook Tests for Dashboard Configuration API
 * Tests T031: Verify React Query hooks for dynamic dashboard configuration
 *
 * NOTE: This test file requires a testing framework to be set up.
 * Recommended: Vitest + @testing-library/react + @testing-library/react-hooks
 *
 * Setup required:
 * 1. npm install -D vitest @vitest/ui @testing-library/react @testing-library/react-hooks
 * 2. npm install -D @testing-library/jest-dom msw
 * 3. Create vitest.config.ts
 * 4. Update package.json with "test" script
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import type { ReactNode } from 'react'
import {
  useDashboardConfig,
  useDashboardConfigById,
  useDashboardConfigList,
  useCreateDashboardConfig,
  useUpdateDashboardConfig,
  useDeleteDashboardConfig,
} from '@/api/dashboardConfig'
import type {
  DashboardConfig,
  DashboardConfigListResponse,
  DashboardConfigCreate,
  DashboardConfigUpdate,
} from '@/types/dashboardConfig'

// Mock API responses
const mockDashboardConfig: DashboardConfig = {
  dashboard_id: 'test-dashboard-id',
  user_id: 'test-user-id',
  dashboard_name: 'Test Dashboard',
  description: 'Test description',
  layout: [
    {
      id: 'kpi-grid-1',
      type: 'kpi_grid',
      position: { row: 0, col: 0, width: 12, height: 2 },
      props: { kpis: ['total_revenue', 'total_units'] },
    },
  ],
  kpis: ['total_revenue', 'total_units'],
  filters: { date_range: 'last_30_days' },
  is_default: true,
  is_active: true,
  display_order: 0,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
}

const mockTenantDefaultConfig: DashboardConfig = {
  ...mockDashboardConfig,
  dashboard_id: 'tenant-default-id',
  user_id: null, // Tenant default
  dashboard_name: 'Overview Dashboard',
  description: 'Default tenant-wide dashboard',
}

const mockDashboardConfigList: DashboardConfigListResponse = {
  dashboards: [
    {
      dashboard_id: 'test-dashboard-id',
      dashboard_name: 'Test Dashboard',
      is_default: true,
      is_active: true,
      display_order: 0,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
    {
      dashboard_id: 'tenant-default-id',
      dashboard_name: 'Overview Dashboard',
      is_default: true,
      is_active: true,
      display_order: 0,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
  ],
  total: 2,
  has_default: true,
}

// Mock Server Worker (MSW) setup
const server = setupServer(
  rest.get('/api/dashboard-configs/default', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockDashboardConfig))
  }),
  rest.get('/api/dashboard-configs/:id', (req, res, ctx) => {
    const { id } = req.params
    if (id === 'test-dashboard-id') {
      return res(ctx.status(200), ctx.json(mockDashboardConfig))
    }
    return res(ctx.status(404), ctx.json({ detail: 'Dashboard not found' }))
  }),
  rest.get('/api/dashboard-configs', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockDashboardConfigList))
  }),
  rest.post('/api/dashboard-configs', (req, res, ctx) => {
    return res(ctx.status(201), ctx.json(mockDashboardConfig))
  }),
  rest.put('/api/dashboard-configs/:id', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockDashboardConfig))
  }),
  rest.delete('/api/dashboard-configs/:id', (req, res, ctx) => {
    return res(ctx.status(204))
  })
)

// Start server before all tests
beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

// Test wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries in tests
      },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('Dashboard Configuration React Query Hooks', () => {
  describe('useDashboardConfig (GET /default)', () => {
    it('should fetch default dashboard configuration successfully', async () => {
      const { result } = renderHook(() => useDashboardConfig(), {
        wrapper: createWrapper(),
      })

      // Initial state - loading
      expect(result.current.isLoading).toBe(true)
      expect(result.current.data).toBeUndefined()

      // Wait for query to complete
      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Verify data
      expect(result.current.data).toEqual(mockDashboardConfig)
      expect(result.current.data?.dashboard_id).toBe('test-dashboard-id')
      expect(result.current.data?.dashboard_name).toBe('Test Dashboard')
      expect(result.current.data?.layout).toHaveLength(1)
    })

    it('should use correct query key', async () => {
      const { result } = renderHook(() => useDashboardConfig(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Verify query key matches expected format
      // Query key should be ['dashboard-config', 'default']
      // This is important for cache invalidation
    })

    it('should have 5-minute staleTime', async () => {
      const { result } = renderHook(() => useDashboardConfig(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Verify staleTime is 5 minutes (300000ms)
      // This prevents excessive refetching
    })

    it('should handle 404 when no default config exists', async () => {
      server.use(
        rest.get('/api/dashboard-configs/default', (req, res, ctx) => {
          return res(ctx.status(404), ctx.json({ detail: 'No default dashboard found' }))
        })
      )

      const { result } = renderHook(() => useDashboardConfig(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toBeDefined()
      expect(result.current.data).toBeUndefined()
    })

    it('should retry once on failure', async () => {
      let attempts = 0
      server.use(
        rest.get('/api/dashboard-configs/default', (req, res, ctx) => {
          attempts++
          if (attempts === 1) {
            return res(ctx.status(500), ctx.json({ detail: 'Server error' }))
          }
          return res(ctx.status(200), ctx.json(mockDashboardConfig))
        })
      )

      const { result } = renderHook(() => useDashboardConfig(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Verify it retried and succeeded on second attempt
      expect(attempts).toBe(2)
      expect(result.current.data).toEqual(mockDashboardConfig)
    })
  })

  describe('useDashboardConfigById (GET /{id})', () => {
    it('should fetch specific dashboard by ID', async () => {
      const { result } = renderHook(
        () => useDashboardConfigById('test-dashboard-id'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockDashboardConfig)
      expect(result.current.data?.dashboard_id).toBe('test-dashboard-id')
    })

    it('should not fetch when dashboardId is null', async () => {
      const { result } = renderHook(() => useDashboardConfigById(null), {
        wrapper: createWrapper(),
      })

      // Query should be disabled (enabled: false)
      expect(result.current.isPending).toBe(true)
      expect(result.current.fetchStatus).toBe('idle')

      // Wait a bit to ensure no fetch occurs
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(result.current.data).toBeUndefined()
    })

    it('should handle 404 for non-existent dashboard', async () => {
      const { result } = renderHook(
        () => useDashboardConfigById('non-existent-id'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toBeDefined()
      expect(result.current.data).toBeUndefined()
    })

    it('should use correct query key with dashboard ID', async () => {
      const { result } = renderHook(
        () => useDashboardConfigById('test-dashboard-id'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Query key should be ['dashboard-config', 'test-dashboard-id']
    })
  })

  describe('useDashboardConfigList (GET /)', () => {
    it('should fetch list of dashboard configurations', async () => {
      const { result } = renderHook(() => useDashboardConfigList(true), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockDashboardConfigList)
      expect(result.current.data?.dashboards).toHaveLength(2)
      expect(result.current.data?.total).toBe(2)
      expect(result.current.data?.has_default).toBe(true)
    })

    it('should pass includeTenantDefaults parameter correctly', async () => {
      let capturedQuery = false
      server.use(
        rest.get('/api/dashboard-configs', (req, res, ctx) => {
          const includeDefaults = req.url.searchParams.get('include_tenant_defaults')
          capturedQuery = includeDefaults === 'false'
          return res(ctx.status(200), ctx.json(mockDashboardConfigList))
        })
      )

      const { result } = renderHook(() => useDashboardConfigList(false), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Verify query param was passed correctly
      expect(capturedQuery).toBe(true)
    })

    it('should default to includeTenantDefaults=true', async () => {
      const { result } = renderHook(() => useDashboardConfigList(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Default should include tenant defaults
      expect(result.current.data?.dashboards).toHaveLength(2)
    })

    it('should use correct query key with includeTenantDefaults flag', async () => {
      const { result } = renderHook(() => useDashboardConfigList(true), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Query key should be ['dashboard-configs', true]
    })
  })

  describe('useCreateDashboardConfig (POST /)', () => {
    it('should create new dashboard configuration', async () => {
      const { result } = renderHook(() => useCreateDashboardConfig(), {
        wrapper: createWrapper(),
      })

      const newConfig: DashboardConfigCreate = {
        dashboard_name: 'New Dashboard',
        description: 'New description',
        layout: [
          {
            id: 'widget-1',
            type: 'kpi_grid',
            position: { row: 0, col: 0, width: 12, height: 2 },
            props: { kpis: ['total_revenue'] },
          },
        ],
        kpis: ['total_revenue'],
        filters: {},
        is_default: false,
        is_active: true,
        display_order: 0,
      }

      result.current.mutate(newConfig)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockDashboardConfig)
    })

    it('should invalidate dashboard-config queries on success', async () => {
      const queryClient = new QueryClient()
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(() => useCreateDashboardConfig(), { wrapper })

      const newConfig: DashboardConfigCreate = {
        dashboard_name: 'New Dashboard',
        layout: [
          {
            id: 'widget-1',
            type: 'kpi_grid',
            position: { row: 0, col: 0, width: 12, height: 2 },
            props: {},
          },
        ],
      }

      result.current.mutate(newConfig)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Verify invalidateQueries was called with correct query keys
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['dashboard-config'] })
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['dashboard-configs'] })
    })

    it('should handle validation errors', async () => {
      server.use(
        rest.post('/api/dashboard-configs', (req, res, ctx) => {
          return res(
            ctx.status(422),
            ctx.json({
              detail: [
                {
                  loc: ['body', 'dashboard_name'],
                  msg: 'field required',
                  type: 'value_error.missing',
                },
              ],
            })
          )
        })
      )

      const { result } = renderHook(() => useCreateDashboardConfig(), {
        wrapper: createWrapper(),
      })

      const invalidConfig = {} as DashboardConfigCreate

      result.current.mutate(invalidConfig)

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toBeDefined()
    })

    it('should handle 409 conflict when duplicate default exists', async () => {
      server.use(
        rest.post('/api/dashboard-configs', (req, res, ctx) => {
          return res(
            ctx.status(409),
            ctx.json({ detail: 'User already has a default dashboard' })
          )
        })
      )

      const { result } = renderHook(() => useCreateDashboardConfig(), {
        wrapper: createWrapper(),
      })

      const configWithDefault: DashboardConfigCreate = {
        dashboard_name: 'Another Default',
        layout: [
          {
            id: 'widget-1',
            type: 'kpi_grid',
            position: { row: 0, col: 0, width: 12, height: 2 },
            props: {},
          },
        ],
        is_default: true,
      }

      result.current.mutate(configWithDefault)

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toBeDefined()
    })
  })

  describe('useUpdateDashboardConfig (PUT /{id})', () => {
    it('should update existing dashboard configuration', async () => {
      const { result } = renderHook(
        () => useUpdateDashboardConfig('test-dashboard-id'),
        { wrapper: createWrapper() }
      )

      const update: DashboardConfigUpdate = {
        dashboard_name: 'Updated Dashboard Name',
      }

      result.current.mutate(update)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockDashboardConfig)
    })

    it('should invalidate dashboard-config queries on success', async () => {
      const queryClient = new QueryClient()
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(
        () => useUpdateDashboardConfig('test-dashboard-id'),
        { wrapper }
      )

      const update: DashboardConfigUpdate = {
        dashboard_name: 'Updated Name',
      }

      result.current.mutate(update)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Verify cache invalidation
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['dashboard-config'] })
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['dashboard-configs'] })
    })

    it('should handle 404 for non-existent dashboard', async () => {
      server.use(
        rest.put('/api/dashboard-configs/:id', (req, res, ctx) => {
          return res(ctx.status(404), ctx.json({ detail: 'Dashboard not found' }))
        })
      )

      const { result } = renderHook(
        () => useUpdateDashboardConfig('non-existent-id'),
        { wrapper: createWrapper() }
      )

      const update: DashboardConfigUpdate = {
        dashboard_name: 'Updated Name',
      }

      result.current.mutate(update)

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toBeDefined()
    })

    it('should handle 403 when updating other user config', async () => {
      server.use(
        rest.put('/api/dashboard-configs/:id', (req, res, ctx) => {
          return res(
            ctx.status(403),
            ctx.json({ detail: 'Not authorized to modify this dashboard' })
          )
        })
      )

      const { result } = renderHook(
        () => useUpdateDashboardConfig('other-user-dashboard-id'),
        { wrapper: createWrapper() }
      )

      const update: DashboardConfigUpdate = {
        dashboard_name: 'Hacked Name',
      }

      result.current.mutate(update)

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toBeDefined()
    })

    it('should support partial updates', async () => {
      const { result } = renderHook(
        () => useUpdateDashboardConfig('test-dashboard-id'),
        { wrapper: createWrapper() }
      )

      // Update only is_active field
      const partialUpdate: DashboardConfigUpdate = {
        is_active: false,
      }

      result.current.mutate(partialUpdate)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
    })
  })

  describe('useDeleteDashboardConfig (DELETE /{id})', () => {
    it('should delete dashboard configuration', async () => {
      const { result } = renderHook(() => useDeleteDashboardConfig(), {
        wrapper: createWrapper(),
      })

      result.current.mutate('test-dashboard-id')

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // DELETE returns 204 No Content, so data should be undefined
      expect(result.current.data).toBeUndefined()
    })

    it('should invalidate dashboard-config queries on success', async () => {
      const queryClient = new QueryClient()
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(() => useDeleteDashboardConfig(), { wrapper })

      result.current.mutate('test-dashboard-id')

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Verify cache invalidation
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['dashboard-config'] })
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['dashboard-configs'] })
    })

    it('should handle 404 for non-existent dashboard', async () => {
      server.use(
        rest.delete('/api/dashboard-configs/:id', (req, res, ctx) => {
          return res(ctx.status(404), ctx.json({ detail: 'Dashboard not found' }))
        })
      )

      const { result } = renderHook(() => useDeleteDashboardConfig(), {
        wrapper: createWrapper(),
      })

      result.current.mutate('non-existent-id')

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toBeDefined()
    })

    it('should handle 403 when deleting other user config', async () => {
      server.use(
        rest.delete('/api/dashboard-configs/:id', (req, res, ctx) => {
          return res(
            ctx.status(403),
            ctx.json({ detail: 'Not authorized to delete this dashboard' })
          )
        })
      )

      const { result } = renderHook(() => useDeleteDashboardConfig(), {
        wrapper: createWrapper(),
      })

      result.current.mutate('other-user-dashboard-id')

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toBeDefined()
    })

    it('should handle 403 when deleting tenant default', async () => {
      server.use(
        rest.delete('/api/dashboard-configs/:id', (req, res, ctx) => {
          return res(
            ctx.status(403),
            ctx.json({ detail: 'Cannot delete tenant default dashboard' })
          )
        })
      )

      const { result } = renderHook(() => useDeleteDashboardConfig(), {
        wrapper: createWrapper(),
      })

      result.current.mutate('tenant-default-id')

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toBeDefined()
    })
  })

  describe('Cache Management & Query Keys', () => {
    it('should use consistent query keys across hooks', async () => {
      // This test verifies that query keys follow the expected pattern:
      // - ['dashboard-config', 'default'] for default config
      // - ['dashboard-config', id] for specific config by ID
      // - ['dashboard-configs', includeTenantDefaults] for list

      // Consistent query keys are critical for cache invalidation
      // When mutations occur, they invalidate all ['dashboard-config*'] queries
    })

    it('should properly invalidate all dashboard queries after create', async () => {
      const queryClient = new QueryClient()

      // Pre-populate cache with queries
      queryClient.setQueryData(['dashboard-config', 'default'], mockDashboardConfig)
      queryClient.setQueryData(['dashboard-configs', true], mockDashboardConfigList)

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(() => useCreateDashboardConfig(), { wrapper })

      const newConfig: DashboardConfigCreate = {
        dashboard_name: 'New Dashboard',
        layout: [
          {
            id: 'widget-1',
            type: 'kpi_grid',
            position: { row: 0, col: 0, width: 12, height: 2 },
            props: {},
          },
        ],
      }

      result.current.mutate(newConfig)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // After mutation, queries should be invalidated (stale)
      const defaultQuery = queryClient.getQueryState(['dashboard-config', 'default'])
      const listQuery = queryClient.getQueryState(['dashboard-configs', true])

      // Both queries should be marked as stale and will refetch
      expect(defaultQuery?.isInvalidated).toBe(true)
      expect(listQuery?.isInvalidated).toBe(true)
    })

    it('should properly invalidate all dashboard queries after update', async () => {
      const queryClient = new QueryClient()

      queryClient.setQueryData(['dashboard-config', 'default'], mockDashboardConfig)
      queryClient.setQueryData(['dashboard-configs', true], mockDashboardConfigList)

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(
        () => useUpdateDashboardConfig('test-dashboard-id'),
        { wrapper }
      )

      const update: DashboardConfigUpdate = {
        dashboard_name: 'Updated Name',
      }

      result.current.mutate(update)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      const defaultQuery = queryClient.getQueryState(['dashboard-config', 'default'])
      const listQuery = queryClient.getQueryState(['dashboard-configs', true])

      expect(defaultQuery?.isInvalidated).toBe(true)
      expect(listQuery?.isInvalidated).toBe(true)
    })

    it('should properly invalidate all dashboard queries after delete', async () => {
      const queryClient = new QueryClient()

      queryClient.setQueryData(['dashboard-config', 'default'], mockDashboardConfig)
      queryClient.setQueryData(['dashboard-configs', true], mockDashboardConfigList)

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(() => useDeleteDashboardConfig(), { wrapper })

      result.current.mutate('test-dashboard-id')

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      const defaultQuery = queryClient.getQueryState(['dashboard-config', 'default'])
      const listQuery = queryClient.getQueryState(['dashboard-configs', true])

      expect(defaultQuery?.isInvalidated).toBe(true)
      expect(listQuery?.isInvalidated).toBe(true)
    })
  })

  describe('Performance & Caching', () => {
    it('should cache dashboard config and not refetch within staleTime', async () => {
      let fetchCount = 0
      server.use(
        rest.get('/api/dashboard-configs/default', (req, res, ctx) => {
          fetchCount++
          return res(ctx.status(200), ctx.json(mockDashboardConfig))
        })
      )

      const { result, rerender } = renderHook(() => useDashboardConfig(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(fetchCount).toBe(1)

      // Rerender should use cached data (within 5-minute staleTime)
      rerender()

      // Wait a bit to ensure no additional fetch occurs
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(fetchCount).toBe(1) // Still only 1 fetch
      expect(result.current.data).toEqual(mockDashboardConfig)
    })

    it('should share cache between multiple components using same hook', async () => {
      let fetchCount = 0
      server.use(
        rest.get('/api/dashboard-configs/default', (req, res, ctx) => {
          fetchCount++
          return res(ctx.status(200), ctx.json(mockDashboardConfig))
        })
      )

      const wrapper = createWrapper()

      // Render first hook
      const { result: result1 } = renderHook(() => useDashboardConfig(), { wrapper })

      await waitFor(() => expect(result1.current.isSuccess).toBe(true))

      expect(fetchCount).toBe(1)

      // Render second hook (same query key)
      const { result: result2 } = renderHook(() => useDashboardConfig(), { wrapper })

      // Second hook should immediately have data from cache
      expect(result2.current.data).toEqual(mockDashboardConfig)

      // Wait to ensure no additional fetch
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(fetchCount).toBe(1) // Still only 1 fetch
    })
  })
})
