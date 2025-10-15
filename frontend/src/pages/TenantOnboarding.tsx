/**
 * Tenant Onboarding Page
 *
 * Admin interface for creating new tenants
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { createTenant, testSupabaseConnection } from '@/api/tenants'
import type { TenantFormData } from '@/types/tenant'

export function TenantOnboarding() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [testingConnection, setTestingConnection] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<{
    tested: boolean
    success: boolean
    message: string
  } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const [formData, setFormData] = useState<TenantFormData>({
    subdomain: '',
    company_name: '',
    database_url: '',
    anon_key: '',
    service_key: '',
    admin_email: '',
    admin_name: '',
  })

  const handleInputChange = (field: keyof TenantFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    setError(null)
    // Reset connection status if database credentials change
    if (field === 'database_url' || field === 'anon_key') {
      setConnectionStatus(null)
    }
  }

  const handleTestConnection = async () => {
    if (!formData.database_url || !formData.anon_key) {
      setError('Please provide both Database URL and Anon Key to test connection')
      return
    }

    setTestingConnection(true)
    setError(null)

    try {
      const result = await testSupabaseConnection(
        formData.database_url,
        formData.anon_key
      )
      setConnectionStatus({
        tested: true,
        success: result.success,
        message: result.message,
      })
    } catch (err) {
      setConnectionStatus({
        tested: true,
        success: false,
        message: err instanceof Error ? err.message : 'Connection test failed',
      })
    } finally {
      setTestingConnection(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    // Validation
    if (!formData.subdomain || !formData.company_name || !formData.database_url) {
      setError('Please fill in all required fields')
      setLoading(false)
      return
    }

    if (!formData.anon_key || !formData.service_key) {
      setError('Please provide both Supabase keys')
      setLoading(false)
      return
    }

    if (!formData.admin_email) {
      setError('Please provide an admin email address')
      setLoading(false)
      return
    }

    // Recommend testing connection first
    if (!connectionStatus?.success) {
      setError('Please test the database connection before creating the tenant')
      setLoading(false)
      return
    }

    try {
      await createTenant({
        subdomain: formData.subdomain.toLowerCase().trim(),
        company_name: formData.company_name.trim(),
        database_url: formData.database_url.trim(),
        database_credentials: {
          anon_key: formData.anon_key.trim(),
          service_key: formData.service_key.trim(),
        },
        admin_email: formData.admin_email.toLowerCase().trim(),
        admin_name: formData.admin_name.trim() || undefined,
      })

      setSuccess(true)

      // Redirect to tenant list after 2 seconds
      setTimeout(() => {
        navigate('/admin/tenants')
      }, 2000)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create tenant'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="space-y-8 animate-in fade-in-0 duration-500">
        <Card className="border-border bg-card shadow-sm">
          <CardContent className="flex flex-col items-center justify-center p-16">
            <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-green-500/20 to-green-500/10 flex items-center justify-center border border-green-500/30 shadow-lg mb-6">
              <CheckCircle2 className="h-10 w-10 text-green-500" />
            </div>
            <p className="text-xl font-semibold text-foreground mb-2">Tenant Created Successfully!</p>
            <p className="text-sm text-muted-foreground text-center max-w-md">
              Redirecting to tenant list...
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-in fade-in-0 duration-500">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center border border-primary/30 shadow-sm">
          <Building2 className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">Create New Tenant</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Onboard a new customer to the platform (~25 minutes)
          </p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Tenant Information */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader>
            <CardTitle>Tenant Information</CardTitle>
            <CardDescription>
              Basic information about the new customer organization
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="subdomain">
                  Subdomain <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="subdomain"
                  placeholder="bibbi"
                  value={formData.subdomain}
                  onChange={(e) => handleInputChange('subdomain', e.target.value)}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  {formData.subdomain
                    ? `https://${formData.subdomain}.taskifai.com`
                    : 'Unique subdomain for tenant access'}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_name">
                  Company Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="company_name"
                  placeholder="BIBBI AB"
                  value={formData.company_name}
                  onChange={(e) => handleInputChange('company_name', e.target.value)}
                  required
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Database Configuration */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader>
            <CardTitle>Supabase Database Configuration</CardTitle>
            <CardDescription>
              Connect to the tenant's Supabase project (created manually beforehand)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="database_url">
                Database URL <span className="text-destructive">*</span>
              </Label>
              <Input
                id="database_url"
                placeholder="https://xxxxxxxxx.supabase.co"
                value={formData.database_url}
                onChange={(e) => handleInputChange('database_url', e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="anon_key">
                Anon Key <span className="text-destructive">*</span>
              </Label>
              <Input
                id="anon_key"
                type="password"
                placeholder="eyJhbGc..."
                value={formData.anon_key}
                onChange={(e) => handleInputChange('anon_key', e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="service_key">
                Service Key <span className="text-destructive">*</span>
              </Label>
              <Input
                id="service_key"
                type="password"
                placeholder="eyJhbGc..."
                value={formData.service_key}
                onChange={(e) => handleInputChange('service_key', e.target.value)}
                required
              />
              <p className="text-xs text-muted-foreground">
                Find keys at: Settings &gt; API in Supabase dashboard
              </p>
            </div>

            <div className="flex items-center gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleTestConnection}
                disabled={testingConnection || !formData.database_url || !formData.anon_key}
              >
                {testingConnection && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Test Connection
              </Button>

              {connectionStatus && (
                <Alert
                  variant={connectionStatus.success ? 'default' : 'destructive'}
                  className="flex-1"
                >
                  {connectionStatus.success ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  <AlertDescription>{connectionStatus.message}</AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Admin User */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader>
            <CardTitle>Admin User</CardTitle>
            <CardDescription>Initial administrator for this tenant</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="admin_email">
                  Admin Email <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="admin_email"
                  type="email"
                  placeholder="admin@bibbi.se"
                  value={formData.admin_email}
                  onChange={(e) => handleInputChange('admin_email', e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="admin_name">Admin Name</Label>
                <Input
                  id="admin_name"
                  placeholder="John Doe"
                  value={formData.admin_name}
                  onChange={(e) => handleInputChange('admin_name', e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/tenants')}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={loading || !connectionStatus?.success}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create Tenant
          </Button>
        </div>
      </form>
    </div>
  )
}
