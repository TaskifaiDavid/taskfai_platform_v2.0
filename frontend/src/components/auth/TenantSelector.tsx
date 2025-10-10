/**
 * Tenant Selector Component
 *
 * Displays list of tenants for multi-tenant users (Flow B).
 * User selects tenant, system exchanges temp token for real token,
 * then redirects to tenant dashboard with token in URL.
 */

import { useState } from 'react'
import { Building2, ArrowRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useExchangeToken } from '@/api/auth'
import type { TenantOption } from '@/types'
import { useToast } from '@/hooks/use-toast'

interface TenantSelectorProps {
  tenants: TenantOption[]
  tempToken: string
  email?: string
}

export function TenantSelector({ tenants, tempToken, email }: TenantSelectorProps) {
  const [selectedSubdomain, setSelectedSubdomain] = useState<string | null>(null)
  const { toast } = useToast()
  const exchangeToken = useExchangeToken()

  const handleTenantSelect = async (tenant: TenantOption) => {
    setSelectedSubdomain(tenant.subdomain)

    try {
      // Exchange temp token for tenant-scoped token
      const response = await exchangeToken.mutateAsync({
        temp_token: tempToken,
        selected_subdomain: tenant.subdomain,
      })

      // Redirect to tenant dashboard with token in URL
      // AuthCallback will extract token and store it
      const callbackUrl = `https://${tenant.subdomain}.taskifai.com/auth/callback?token=${response.access_token}`
      window.location.href = callbackUrl

    } catch (error: any) {
      setSelectedSubdomain(null)
      toast({
        title: 'Authentication Error',
        description: error?.response?.data?.detail || 'Failed to authenticate with selected tenant',
        variant: 'destructive',
      })
    }
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
        {tenants.map((tenant) => {
          const isSelecting = selectedSubdomain === tenant.subdomain

          return (
            <Card
              key={tenant.subdomain}
              className={`hover:border-primary hover:shadow-md transition-all ${
                isSelecting ? 'opacity-50 cursor-wait' : 'cursor-pointer'
              }`}
            >
              <Button
                variant="ghost"
                className="w-full h-auto p-4 flex items-center justify-between hover:bg-transparent"
                onClick={() => handleTenantSelect(tenant)}
                disabled={isSelecting || exchangeToken.isPending}
              >
                <div className="flex items-center gap-3">
                  {/* Tenant Icon */}
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                    {isSelecting ? (
                      <Loader2 className="h-5 w-5 text-primary animate-spin" />
                    ) : (
                      <Building2 className="h-5 w-5 text-primary" />
                    )}
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

                {/* Arrow Icon or Loading */}
                {isSelecting ? (
                  <span className="text-sm text-muted-foreground">Redirecting...</span>
                ) : (
                  <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                )}
              </Button>
            </Card>
          )
        })}
      </div>

      <div className="mt-6 pt-6 border-t border-border">
        <p className="text-xs text-center text-muted-foreground">
          Signed in as <span className="font-semibold text-foreground">{email}</span>
        </p>
      </div>
    </div>
  )
}
