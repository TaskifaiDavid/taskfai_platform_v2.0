import { Bell, User, Menu, Search, ChevronRight } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useUIStore } from '@/stores/ui'
import { useLocation } from 'react-router-dom'
import { TenantBadge } from './TenantBadge'
import { Button } from '@/components/ui/button'

const routeNames: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/uploads': 'Uploads',
  '/chat': 'AI Chat',
  '/analytics': 'Analytics',
  '/dashboards': 'Dashboards',
  '/settings': 'Settings',
  '/admin': 'Admin',
}

export function Header() {
  const { user } = useAuth()
  const { toggleSidebar } = useUIStore()
  const location = useLocation()

  const currentPath = location.pathname
  const pageName = routeNames[currentPath] || 'Dashboard'

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-card px-4 md:px-6 shadow-sm">
      <div className="flex items-center gap-4">
        {/* Mobile menu toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="lg:hidden hover:bg-primary/10"
          aria-label="Toggle menu"
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Breadcrumbs */}
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground hidden md:inline font-medium">Home</span>
          <ChevronRight className="h-4 w-4 text-muted-foreground hidden md:inline" />
          <h2 className="font-semibold text-foreground">{pageName}</h2>
        </div>
      </div>

      <div className="flex items-center gap-2 md:gap-3">
        {/* Search - Desktop only */}
        <Button
          variant="ghost"
          size="icon"
          className="hidden md:flex hover:bg-primary/10 hover:text-primary"
        >
          <Search className="h-5 w-5" />
        </Button>

        {/* Tenant Badge - Desktop only */}
        <div className="hidden md:block">
          <TenantBadge />
        </div>

        {/* Notifications */}
        <Button
          variant="ghost"
          size="icon"
          className="relative hover:bg-primary/10 hover:text-primary"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground shadow-sm animate-pulse">
            3
          </span>
        </Button>

        {/* User Profile - Desktop only */}
        <div className="hidden md:flex items-center gap-3 rounded-lg border border-border bg-background/50 px-3 py-2 hover:border-primary/50 transition-colors cursor-pointer">
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center border border-primary/30">
            <span className="text-xs font-bold text-primary">
              {user?.email.substring(0, 2).toUpperCase()}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-foreground">{user?.email}</span>
            <span className="text-xs text-muted-foreground capitalize">{user?.role}</span>
          </div>
        </div>

        {/* User Avatar - Mobile only */}
        <Button variant="ghost" size="icon" className="md:hidden hover:bg-primary/10">
          <div className="h-9 w-9 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center border border-primary/30">
            <span className="text-xs font-bold text-primary">
              {user?.email.substring(0, 2).toUpperCase()}
            </span>
          </div>
        </Button>
      </div>
    </header>
  )
}
