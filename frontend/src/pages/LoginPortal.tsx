/**
 * Login Portal - Central Entry Point
 *
 * Handles tenant discovery for app.taskifai.com
 * Routes users to their organization's subdomain based on email
 */

import { useState, FormEvent } from 'react'
import { Mail, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { TenantSelector } from '@/components/auth/TenantSelector'
import {
  discoverTenant,
  isSingleTenantResponse,
  isMultiTenantResponse,
  isValidTenantUrl,
  type TenantOption
} from '@/api/tenant'

export function LoginPortal() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tenants, setTenants] = useState<TenantOption[] | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const response = await discoverTenant(email)

      // Single tenant → auto-redirect
      if (isSingleTenantResponse(response)) {
        // Validate redirect URL for security
        if (!isValidTenantUrl(response.redirect_url)) {
          setError('Invalid tenant URL received. Please contact support.')
          setLoading(false)
          return
        }

        // Redirect to tenant login page
        window.location.href = response.redirect_url
        return
      }

      // Multiple tenants → show selector
      if (isMultiTenantResponse(response)) {
        setTenants(response.tenants)
        setLoading(false)
        return
      }

      // Unexpected response format
      setError('Unexpected response from server. Please try again.')
      setLoading(false)
    } catch (err: any) {
      setLoading(false)

      // Handle 404 - email not found
      if (err.response?.status === 404) {
        setError('No account found with this email address.')
        return
      }

      // Handle other errors
      if (err.response?.data?.detail) {
        setError(err.response.data.detail)
      } else if (err.message) {
        setError(err.message)
      } else {
        setError('An error occurred. Please try again.')
      }
    }
  }

  // Show tenant selector if multiple tenants found
  if (tenants) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md p-6">
          <TenantSelector tenants={tenants} email={email} />
        </Card>
      </div>
    )
  }

  // Show email input form
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md p-6">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Welcome to TaskifAI
          </h1>
          <p className="text-sm text-muted-foreground">
            Enter your email to access your organization
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email Input */}
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium text-foreground">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                id="email"
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                required
                className="pl-10"
                autoComplete="email"
                autoFocus
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={loading || !email}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Finding your organization...
              </>
            ) : (
              'Continue'
            )}
          </Button>
        </form>

        <div className="mt-6 pt-6 border-t border-border">
          <p className="text-xs text-center text-muted-foreground">
            Don't have an account?{' '}
            <a href="/signup" className="text-primary hover:underline">
              Contact sales
            </a>
          </p>
        </div>
      </Card>
    </div>
  )
}
