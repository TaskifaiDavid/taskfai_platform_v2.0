/**
 * Tenant Selector Component
 *
 * Displays list of tenants for multi-tenant users (Flow B).
 * User is already authenticated, just needs to select tenant.
 * Redirects to dashboard (not login page) with temp token.
 */

import { Building2, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import type { TenantOption } from '@/api/tenant'
import { buildDashboardUrl } from '@/api/loginAndDiscover'

interface TenantSelectorProps {
  tenants: TenantOption[]
  email?: string
}

export function TenantSelector({ tenants, email }: TenantSelectorProps) {
  const handleTenantSelect = (tenant: TenantOption) => {
    // Build dashboard URL (user is already authenticated)
    const dashboardUrl = buildDashboardUrl(tenant.subdomain)

    // TODO: In production, you would exchange temp token for real token here
    // For now, just redirect to dashboard (temp token is in sessionStorage)

    // Redirect to tenant dashboard
    window.location.href = dashboardUrl
  }

  return (
    <div className="w-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Select Your Organization
        </h2>
        <p className="text-sm text-muted-foreground">
          You have access to multiple organizations. Please select one to continue.
        </p>
      </div>

      <div className="space-y-3">
        {tenants.map((tenant) => (
          <Card
            key={tenant.subdomain}
            className="hover:border-primary hover:shadow-md transition-all cursor-pointer"
          >
            <Button
              variant="ghost"
              className="w-full h-auto p-4 flex items-center justify-between hover:bg-transparent"
              onClick={() => handleTenantSelect(tenant)}
            >
              <div className="flex items-center gap-3">
                {/* Tenant Icon */}
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Building2 className="h-5 w-5 text-primary" />
                </div>

                {/* Tenant Info */}
                <div className="text-left">
                  <div className="font-semibold text-foreground">
                    {tenant.company_name}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {tenant.subdomain}.taskifai.com
                  </div>
                </div>
              </div>

              {/* Arrow Icon */}
              <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </Button>
          </Card>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-border">
        <p className="text-xs text-center text-muted-foreground">
          Signed in as <span className="font-semibold text-foreground">{email}</span>
        </p>
      </div>
    </div>
  )
}
