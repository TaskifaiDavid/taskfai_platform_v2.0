/**
 * Frontend Test: Central Login Portal (T015)
 *
 * Tests the central login portal at app.taskifai.com that handles tenant discovery.
 *
 * Flow:
 * 1. User visits app.taskifai.com
 * 2. User enters email address
 * 3. System discovers tenant via POST /api/auth/discover-tenant
 * 4. Single tenant: Redirect to tenant subdomain with email pre-filled
 * 5. Multi-tenant: Show tenant selector
 *
 * Tests MUST FAIL before implementation (TDD).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import CentralLoginPortal from '@/pages/CentralLoginPortal'
import * as api from '@/api/auth'

// Mock API calls
vi.mock('@/api/auth', () => ({
  discoverTenant: vi.fn()
}))

describe('CentralLoginPortal Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render email input form', () => {
    render(
      <BrowserRouter>
        <CentralLoginPortal />
      </BrowserRouter>
    )

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /continue|next|submit/i })).toBeInTheDocument()
  })

  it('should validate email format before submission', async () => {
    render(
      <BrowserRouter>
        <CentralLoginPortal />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /continue|next|submit/i })

    // Try invalid email
    fireEvent.change(emailInput, { target: { value: 'not-an-email' } })
    fireEvent.click(submitButton)

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/invalid email|valid email/i)).toBeInTheDocument()
    })

    // API should not be called
    expect(api.discoverTenant).not.toHaveBeenCalled()
  })

  it('should call tenant discovery API with valid email', async () => {
    const mockDiscoverResponse = {
      subdomain: 'customer1',
      company_name: 'Customer 1 Inc',
      redirect_url: 'https://customer1.taskifai.com/login?email=user@customer1.com'
    }

    vi.mocked(api.discoverTenant).mockResolvedValue(mockDiscoverResponse)

    render(
      <BrowserRouter>
        <CentralLoginPortal />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /continue|next|submit/i })

    // Enter valid email
    fireEvent.change(emailInput, { target: { value: 'user@customer1.com' } })
    fireEvent.click(submitButton)

    // Should call API
    await waitFor(() => {
      expect(api.discoverTenant).toHaveBeenCalledWith({ email: 'user@customer1.com' })
    })
  })

  it('should redirect to tenant subdomain for single tenant user', async () => {
    const mockDiscoverResponse = {
      subdomain: 'customer1',
      company_name: 'Customer 1 Inc',
      redirect_url: 'https://customer1.taskifai.com/login?email=user@customer1.com'
    }

    vi.mocked(api.discoverTenant).mockResolvedValue(mockDiscoverResponse)

    // Mock window.location
    delete (window as any).location
    window.location = { href: '' } as any

    render(
      <BrowserRouter>
        <CentralLoginPortal />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /continue|next|submit/i })

    fireEvent.change(emailInput, { target: { value: 'user@customer1.com' } })
    fireEvent.click(submitButton)

    // Should redirect
    await waitFor(() => {
      expect(window.location.href).toBe(mockDiscoverResponse.redirect_url)
    })
  })

  it('should show tenant selector for multi-tenant user', async () => {
    const mockMultiTenantResponse = {
      tenants: [
        { subdomain: 'customer1', company_name: 'Customer 1 Inc' },
        { subdomain: 'demo', company_name: 'Demo Company' }
      ]
    }

    vi.mocked(api.discoverTenant).mockResolvedValue(mockMultiTenantResponse)

    render(
      <BrowserRouter>
        <CentralLoginPortal />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /continue|next|submit/i })

    fireEvent.change(emailInput, { target: { value: 'david@taskifai.com' } })
    fireEvent.click(submitButton)

    // Should show tenant selector
    await waitFor(() => {
      expect(screen.getByText(/customer 1 inc/i)).toBeInTheDocument()
      expect(screen.getByText(/demo company/i)).toBeInTheDocument()
    })
  })

  it('should show error for email not found in system', async () => {
    vi.mocked(api.discoverTenant).mockRejectedValue({
      response: { status: 404, data: { detail: 'No tenant found for this email' } }
    })

    render(
      <BrowserRouter>
        <CentralLoginPortal />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /continue|next|submit/i })

    fireEvent.change(emailInput, { target: { value: 'unknown@example.com' } })
    fireEvent.click(submitButton)

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/not found|no tenant found/i)).toBeInTheDocument()
    })
  })

  it('should handle API errors gracefully', async () => {
    vi.mocked(api.discoverTenant).mockRejectedValue({
      response: { status: 500, data: { detail: 'Internal server error' } }
    })

    render(
      <BrowserRouter>
        <CentralLoginPortal />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /continue|next|submit/i })

    fireEvent.change(emailInput, { target: { value: 'user@example.com' } })
    fireEvent.click(submitButton)

    // Should show generic error message
    await waitFor(() => {
      expect(screen.getByText(/error|something went wrong/i)).toBeInTheDocument()
    })
  })

  it('should show loading state during API call', async () => {
    // Delay API response
    vi.mocked(api.discoverTenant).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        subdomain: 'customer1',
        company_name: 'Customer 1 Inc',
        redirect_url: 'https://customer1.taskifai.com/login?email=user@customer1.com'
      }), 1000))
    )

    render(
      <BrowserRouter>
        <CentralLoginPortal />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /continue|next|submit/i })

    fireEvent.change(emailInput, { target: { value: 'user@customer1.com' } })
    fireEvent.click(submitButton)

    // Should show loading indicator
    await waitFor(() => {
      expect(screen.getByText(/loading|discovering/i)).toBeInTheDocument()
    })
  })

  it('should disable submit button while loading', async () => {
    vi.mocked(api.discoverTenant).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        subdomain: 'customer1',
        company_name: 'Customer 1 Inc',
        redirect_url: 'https://customer1.taskifai.com/login?email=user@customer1.com'
      }), 1000))
    )

    render(
      <BrowserRouter>
        <CentralLoginPortal />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /continue|next|submit/i }) as HTMLButtonElement

    fireEvent.change(emailInput, { target: { value: 'user@customer1.com' } })
    fireEvent.click(submitButton)

    // Button should be disabled during loading
    await waitFor(() => {
      expect(submitButton.disabled).toBe(true)
    })
  })

  it('should include email in redirect URL query parameter', async () => {
    const email = 'user@customer1.com'
    const mockDiscoverResponse = {
      subdomain: 'customer1',
      company_name: 'Customer 1 Inc',
      redirect_url: `https://customer1.taskifai.com/login?email=${encodeURIComponent(email)}`
    }

    vi.mocked(api.discoverTenant).mockResolvedValue(mockDiscoverResponse)

    delete (window as any).location
    window.location = { href: '' } as any

    render(
      <BrowserRouter>
        <CentralLoginPortal />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /continue|next|submit/i })

    fireEvent.change(emailInput, { target: { value: email } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(window.location.href).toContain(`email=${encodeURIComponent(email)}`)
    })
  })

  it('should have accessible form labels and ARIA attributes', () => {
    render(
      <BrowserRouter>
        <CentralLoginPortal />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)

    // Should have proper ARIA attributes
    expect(emailInput).toHaveAttribute('type', 'email')
    expect(emailInput).toHaveAttribute('required')
    expect(emailInput).toHaveAttribute('aria-required', 'true')
  })
})
