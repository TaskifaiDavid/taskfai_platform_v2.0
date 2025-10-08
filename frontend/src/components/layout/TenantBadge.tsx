import { Badge } from '@/components/ui/badge'
import { useTenant } from '@/hooks/useTenant'
import { Building2 } from 'lucide-react'

export function TenantBadge() {
  const { subdomain, isLocalDev } = useTenant()

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-accent/10 border border-accent/30">
      <Building2 className="h-4 w-4 text-accent" />
      <span className="text-sm font-semibold text-accent">{subdomain}</span>
      {isLocalDev && <span className="text-xs text-accent/70 font-medium">(dev)</span>}
    </div>
  )
}
