/**
 * Tenant List Page
 *
 * Admin interface for viewing and managing all tenants
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, Plus, CheckCircle2, XCircle, Loader2, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { listTenants } from '@/api/tenants'
import type { Tenant } from '@/types/tenant'

export function TenantList() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [total, setTotal] = useState(0)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTenants()
  }, [])

  const loadTenants = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await listTenants({ limit: 100, offset: 0 })
      setTenants(response.tenants)
      setTotal(response.total)
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to load tenants'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  if (loading) {
    return (
      <div className="space-y-8 animate-in fade-in-0 duration-500">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center border border-primary/30 shadow-sm">
            <Building2 className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Tenant Management</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Manage all customer tenants
            </p>
          </div>
        </div>

        <Card className="border-border bg-card shadow-sm">
          <CardContent className="flex items-center justify-center p-16">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-in fade-in-0 duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center border border-primary/30 shadow-sm">
            <Building2 className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Tenant Management</h1>
            <p className="text-sm text-muted-foreground mt-1">
              {total} {total === 1 ? 'tenant' : 'tenants'} registered
            </p>
          </div>
        </div>

        <Button onClick={() => navigate('/admin/tenants/new')}>
          <Plus className="mr-2 h-4 w-4" />
          Create Tenant
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Tenants Table */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader>
          <CardTitle>All Tenants</CardTitle>
          <CardDescription>
            View and manage all customer organizations
          </CardDescription>
        </CardHeader>
        <CardContent>
          {tenants.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-muted/50 to-muted/20 flex items-center justify-center border border-border mb-4">
                <Building2 className="h-8 w-8 text-muted-foreground" />
              </div>
              <p className="text-lg font-semibold text-foreground mb-1">No Tenants Yet</p>
              <p className="text-sm text-muted-foreground text-center max-w-md mb-4">
                Create your first tenant to get started with multi-tenant management
              </p>
              <Button onClick={() => navigate('/admin/tenants/new')}>
                <Plus className="mr-2 h-4 w-4" />
                Create First Tenant
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                      Company
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                      Subdomain
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                      Database
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                      Status
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                      Created
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {tenants.map((tenant) => (
                    <tr
                      key={tenant.tenant_id}
                      className="border-b border-border hover:bg-muted/30 transition-colors"
                    >
                      <td className="py-4 px-4">
                        <div>
                          <p className="font-medium text-foreground">
                            {tenant.company_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            ID: {tenant.tenant_id.slice(0, 8)}...
                          </p>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <a
                          href={`https://${tenant.subdomain}.taskifai.com`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-primary hover:underline"
                        >
                          {tenant.subdomain}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </td>
                      <td className="py-4 px-4">
                        <code className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                          {tenant.database_url.replace('https://', '').slice(0, 20)}...
                        </code>
                      </td>
                      <td className="py-4 px-4">
                        {tenant.is_active ? (
                          <Badge
                            variant="outline"
                            className="border-green-500/30 bg-green-500/10 text-green-600"
                          >
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                            Active
                          </Badge>
                        ) : (
                          <Badge
                            variant="outline"
                            className="border-destructive/30 bg-destructive/10 text-destructive"
                          >
                            <XCircle className="mr-1 h-3 w-3" />
                            Inactive
                          </Badge>
                        )}
                      </td>
                      <td className="py-4 px-4 text-sm text-muted-foreground">
                        {formatDate(tenant.created_at)}
                      </td>
                      <td className="py-4 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/admin/tenants/${tenant.tenant_id}`)}
                        >
                          View Details
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
