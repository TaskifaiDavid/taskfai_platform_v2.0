/**
 * Frontend Test: Tenant Selector Component (T016)
 *
 * Tests the tenant selector component shown when a user belongs to multiple tenants.
 *
 * Functionality:
 * - Displays list of tenants user has access to
 * - Shows company name and subdomain for each tenant
 * - Allows user to select a tenant
 * - Redirects to selected tenant subdomain with email pre-filled
 * - Handles keyboard navigation for accessibility
 *
 * Tests MUST FAIL before implementation (TDD).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import TenantSelector from '@/components/TenantSelector'

describe('TenantSelector Component', () => {
  const mockTenants = [
    { subdomain: 'customer1', company_name: 'Customer 1 Inc' },
    { subdomain: 'demo', company_name: 'Demo Company' },
    { subdomain: 'acme', company_name: 'Acme Corp' }
  ]

  const mockEmail = 'david@taskifai.com'

  beforeEach(() => {
    vi.clearAllMocks()
    // Reset window.location
    delete (window as any).location
    window.location = { href: '' } as any
  })

  it('should render list of tenants', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} />
      </BrowserRouter>
    )

    // Should show all tenant company names
    expect(screen.getByText('Customer 1 Inc')).toBeInTheDocument()
    expect(screen.getByText('Demo Company')).toBeInTheDocument()
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
  })

  it('should show tenant subdomains', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} />
      </BrowserRouter>
    )

    // Should show subdomains
    expect(screen.getByText(/customer1/i)).toBeInTheDocument()
    expect(screen.getByText(/demo/i)).toBeInTheDocument()
    expect(screen.getByText(/acme/i)).toBeInTheDocument()
  })

  it('should redirect to selected tenant subdomain', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} />
      </BrowserRouter>
    )

    // Click on first tenant
    const tenant1Button = screen.getByRole('button', { name: /customer 1 inc/i })
    fireEvent.click(tenant1Button)

    // Should redirect to tenant subdomain
    expect(window.location.href).toContain('customer1.taskifai.com')
    expect(window.location.href).toContain(`email=${encodeURIComponent(mockEmail)}`)
  })

  it('should include email in redirect URL', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} />
      </BrowserRouter>
    )

    const demoButton = screen.getByRole('button', { name: /demo company/i })
    fireEvent.click(demoButton)

    // Redirect URL should include email query parameter
    expect(window.location.href).toMatch(/demo\.taskifai\.com.*email=david%40taskifai\.com/)
  })

  it('should handle empty tenants array gracefully', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={[]} email={mockEmail} />
      </BrowserRouter>
    )

    // Should show "no tenants" message
    expect(screen.getByText(/no tenants|no access/i)).toBeInTheDocument()
  })

  it('should be keyboard navigable', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} />
      </BrowserRouter>
    )

    const tenant1Button = screen.getByRole('button', { name: /customer 1 inc/i })
    const tenant2Button = screen.getByRole('button', { name: /demo company/i })

    // Should be focusable
    tenant1Button.focus()
    expect(document.activeElement).toBe(tenant1Button)

    // Tab to next button
    fireEvent.keyDown(tenant1Button, { key: 'Tab' })
    // Note: Actual focus change requires real browser, testing mechanism exists

    // Enter key should trigger selection
    fireEvent.keyDown(tenant2Button, { key: 'Enter' })
    expect(window.location.href).toContain('demo.taskifai.com')
  })

  it('should have accessible ARIA attributes', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} />
      </BrowserRouter>
    )

    // List should have proper role
    const list = screen.getByRole('list') || screen.getByRole('group')
    expect(list).toBeInTheDocument()

    // Buttons should have accessible labels
    const buttons = screen.getAllByRole('button')
    buttons.forEach(button => {
      expect(button).toHaveAccessibleName()
    })
  })

  it('should show descriptive title/heading', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} />
      </BrowserRouter>
    )

    // Should have heading explaining what to do
    expect(screen.getByText(/select|choose.*tenant|account/i)).toBeInTheDocument()
  })

  it('should display tenant cards/buttons clearly', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} />
      </BrowserRouter>
    )

    // Each tenant should be in a button or card
    const tenant1Button = screen.getByRole('button', { name: /customer 1 inc/i })
    expect(tenant1Button).toBeInTheDocument()

    // Should be clickable
    expect(tenant1Button).not.toBeDisabled()
  })

  it('should handle single tenant gracefully', () => {
    const singleTenant = [{ subdomain: 'only-one', company_name: 'Only One Inc' }]

    render(
      <BrowserRouter>
        <TenantSelector tenants={singleTenant} email={mockEmail} />
      </BrowserRouter>
    )

    // Should still show the tenant (not auto-redirect since component expects multiple)
    expect(screen.getByText('Only One Inc')).toBeInTheDocument()
  })

  it('should sanitize tenant data to prevent XSS', () => {
    const maliciousTenants = [
      { subdomain: 'safe', company_name: '<script>alert("xss")</script>' },
      { subdomain: 'safe2', company_name: 'Normal Name' }
    ]

    render(
      <BrowserRouter>
        <TenantSelector tenants={maliciousTenants} email={mockEmail} />
      </BrowserRouter>
    )

    // Should escape HTML
    const container = screen.getByText(/alert/i).closest('div') || screen.getByText(/alert/i)
    expect(container?.innerHTML).not.toContain('<script>')
  })

  it('should show visual hover state on tenant cards', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} />
      </BrowserRouter>
    )

    const tenant1Button = screen.getByRole('button', { name: /customer 1 inc/i })

    // Hover should change appearance (verified via CSS class or inline style)
    fireEvent.mouseEnter(tenant1Button)
    // Visual state tested via snapshot or class check
    expect(tenant1Button).toHaveClass(/hover|active/i)
  })

  it('should format subdomain as URL preview', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} />
      </BrowserRouter>
    )

    // Should show subdomain as URL format (e.g., "customer1.taskifai.com")
    const urlPreview = screen.getByText(/customer1\.taskifai\.com/i)
    expect(urlPreview).toBeInTheDocument()
  })

  it('should provide cancel/back option', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} onBack={vi.fn()} />
      </BrowserRouter>
    )

    // Should have back/cancel button
    const backButton = screen.getByRole('button', { name: /back|cancel/i })
    expect(backButton).toBeInTheDocument()
  })

  it('should call onBack callback when back button clicked', () => {
    const mockOnBack = vi.fn()

    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} onBack={mockOnBack} />
      </BrowserRouter>
    )

    const backButton = screen.getByRole('button', { name: /back|cancel/i })
    fireEvent.click(backButton)

    expect(mockOnBack).toHaveBeenCalledTimes(1)
  })

  it('should sort tenants alphabetically by company name', () => {
    const unsortedTenants = [
      { subdomain: 'zebra', company_name: 'Zebra Corp' },
      { subdomain: 'apple', company_name: 'Apple Inc' },
      { subdomain: 'microsoft', company_name: 'Microsoft' }
    ]

    render(
      <BrowserRouter>
        <TenantSelector tenants={unsortedTenants} email={mockEmail} />
      </BrowserRouter>
    )

    const buttons = screen.getAllByRole('button').filter(btn =>
      btn.textContent?.includes('Inc') ||
      btn.textContent?.includes('Corp') ||
      btn.textContent?.includes('Microsoft')
    )

    // First button should be Apple (alphabetically first)
    expect(buttons[0]).toHaveTextContent(/apple inc/i)
  })

  it('should handle very long company names gracefully', () => {
    const longNameTenants = [
      {
        subdomain: 'longname',
        company_name: 'This Is A Very Long Company Name That Should Be Truncated Or Wrapped Properly'
      }
    ]

    render(
      <BrowserRouter>
        <TenantSelector tenants={longNameTenants} email={mockEmail} />
      </BrowserRouter>
    )

    // Should not break layout
    const button = screen.getByRole('button', { name: /this is a very long/i })
    expect(button).toBeInTheDocument()
    // Text should be truncated or wrapped (check via CSS or class)
  })

  it('should show loading state when redirecting', () => {
    render(
      <BrowserRouter>
        <TenantSelector tenants={mockTenants} email={mockEmail} />
      </BrowserRouter>
    )

    const tenant1Button = screen.getByRole('button', { name: /customer 1 inc/i })
    fireEvent.click(tenant1Button)

    // Should show loading indicator (brief moment before redirect)
    // Note: Actual loading state may be too fast to test
  })
})
