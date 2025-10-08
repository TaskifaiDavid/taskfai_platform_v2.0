import { useMemo } from 'react'

export interface TenantInfo {
  subdomain: string
  isLocalDev: boolean
}

export function useTenant(): TenantInfo {
  const tenantInfo = useMemo(() => {
    const hostname = window.location.hostname

    // Check if localhost or IP
    const isLocalDev = hostname === 'localhost' || /^\d+\.\d+\.\d+\.\d+$/.test(hostname)

    if (isLocalDev) {
      return {
        subdomain: 'demo',
        isLocalDev: true,
      }
    }

    // Extract subdomain from hostname (e.g., tenant1.taskifai.com -> tenant1)
    const parts = hostname.split('.')
    const subdomain = parts.length >= 3 ? parts[0] : 'demo'

    return {
      subdomain,
      isLocalDev: false,
    }
  }, [])

  return tenantInfo
}
