import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Upload,
  MessageSquare,
  BarChart3,
  Monitor,
  Settings,
  LogOut,
  Shield,
  Sparkles,
  ChevronLeft,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useUIStore } from '@/stores/ui'
import { Button } from '@/components/ui/button'

interface SidebarProps {
  className?: string
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, description: 'Overview & KPIs' },
  { name: 'Uploads', href: '/uploads', icon: Upload, description: 'Manage data files' },
  { name: 'AI Chat', href: '/chat', icon: MessageSquare, description: 'Ask questions', badge: 'AI' },
  { name: 'Analytics', href: '/analytics', icon: BarChart3, description: 'Detailed insights' },
  { name: 'External Dashboards', href: '/dashboards', icon: Monitor, description: 'External BI tools' },
]

const adminNavigation = [
  { name: 'Admin', href: '/admin', icon: Shield, description: 'System settings' },
]

export function Sidebar({ className }: SidebarProps) {
  const { user, logout } = useAuth()
  const { sidebarOpen, toggleSidebar } = useUIStore()
  const isAdmin = user?.role === 'admin'

  return (
    <div
      className={cn(
        'flex h-full flex-col border-r transition-all duration-300',
        'bg-[hsl(var(--sidebar-background))] text-[hsl(var(--sidebar-foreground))] border-[hsl(var(--sidebar-border))]',
        sidebarOpen ? 'w-72' : 'w-20',
        className
      )}
    >
      {/* Logo & Toggle */}
      <div className="flex h-16 items-center justify-between border-b border-[hsl(var(--sidebar-border))] px-4">
        <div className={cn("flex items-center gap-3", !sidebarOpen && "mx-auto")}>
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center flex-shrink-0 border border-primary/30">
            <Sparkles className="h-5 w-5 text-primary" />
          </div>
          {sidebarOpen && (
            <div>
              <h1 className="text-lg font-bold text-[hsl(var(--sidebar-foreground))]">TaskifAI</h1>
              <p className="text-xs text-[hsl(var(--sidebar-foreground))]/50">Analytics Platform</p>
            </div>
          )}
        </div>
        {sidebarOpen && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="h-8 w-8 hover:bg-[hsl(var(--sidebar-foreground))]/10 text-[hsl(var(--sidebar-foreground))]/60 hover:text-[hsl(var(--sidebar-foreground))]"
            aria-label="Collapse sidebar"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* User Info */}
      {user && sidebarOpen && (
        <div className="px-4 py-4 border-b border-[hsl(var(--sidebar-border))]">
          <div className="flex items-center gap-3 p-3 rounded-lg bg-[hsl(var(--sidebar-foreground))]/5 border border-[hsl(var(--sidebar-foreground))]/10">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center flex-shrink-0 border border-primary/30">
              <span className="text-sm font-bold text-primary">
                {user.email.substring(0, 2).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold truncate text-[hsl(var(--sidebar-foreground))]">{user.email}</p>
              <p className="text-xs text-[hsl(var(--sidebar-foreground))]/60 capitalize flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent"></span>
                {user.role}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
        <div className="space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              title={!sidebarOpen ? item.name : undefined}
              className={({ isActive }) =>
                cn(
                  'group flex items-center gap-3 rounded-lg text-sm font-medium transition-all duration-200 relative',
                  sidebarOpen ? 'px-3 py-3' : 'px-3 py-3 justify-center',
                  isActive
                    ? 'bg-gradient-to-r from-primary/15 to-accent/10 text-primary border-l-2 border-accent shadow-sm'
                    : 'text-[hsl(var(--sidebar-foreground))]/70 hover:bg-[hsl(var(--sidebar-foreground))]/8 hover:text-[hsl(var(--sidebar-foreground))] hover:border-l-2 hover:border-primary/50'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon className={cn(
                    "h-5 w-5 flex-shrink-0 transition-all duration-200",
                    isActive ? "text-primary scale-110" : "group-hover:scale-110"
                  )} />
                  {sidebarOpen && (
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="truncate">{item.name}</span>
                        {item.badge && (
                          <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-gradient-to-r from-accent to-accent/80 text-white flex-shrink-0 shadow-sm">
                            {item.badge}
                          </span>
                        )}
                      </div>
                      {sidebarOpen && (
                        <p className={cn(
                          "text-xs transition-colors truncate mt-0.5",
                          isActive ? "text-primary/80" : "text-[hsl(var(--sidebar-foreground))]/50"
                        )}>
                          {item.description}
                        </p>
                      )}
                    </div>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </div>

        {isAdmin && (
          <>
            <div className="my-4 border-t border-[hsl(var(--sidebar-border))]" />
            <div className="space-y-1">
              {sidebarOpen && (
                <p className="px-3 text-xs font-semibold text-[hsl(var(--sidebar-foreground))]/50 uppercase tracking-wider mb-2">
                  Administration
                </p>
              )}
              {adminNavigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  title={!sidebarOpen ? item.name : undefined}
                  className={({ isActive }) =>
                    cn(
                      'group flex items-center gap-3 rounded-lg text-sm font-medium transition-all duration-200',
                      sidebarOpen ? 'px-3 py-3' : 'px-3 py-3 justify-center',
                      isActive
                        ? 'bg-gradient-to-r from-destructive/20 to-destructive/10 text-destructive border-l-2 border-destructive'
                        : 'text-[hsl(var(--sidebar-foreground))]/70 hover:bg-[hsl(var(--sidebar-foreground))]/8 hover:text-[hsl(var(--sidebar-foreground))]'
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      <item.icon className={cn(
                        "h-5 w-5 flex-shrink-0 transition-all duration-200",
                        isActive ? "text-destructive scale-110" : "group-hover:scale-110"
                      )} />
                      {sidebarOpen && (
                        <div className="flex-1 min-w-0">
                          <span className="truncate">{item.name}</span>
                          <p className={cn(
                            "text-xs transition-colors truncate mt-0.5",
                            isActive ? "text-destructive/80" : "text-[hsl(var(--sidebar-foreground))]/50"
                          )}>
                            {item.description}
                          </p>
                        </div>
                      )}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </>
        )}
      </nav>

      {/* Settings & Logout */}
      <div className="border-t border-[hsl(var(--sidebar-border))] p-3 space-y-1">
        {!sidebarOpen && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="w-full h-12 hover:bg-[hsl(var(--sidebar-foreground))]/8 text-[hsl(var(--sidebar-foreground))]/60 hover:text-[hsl(var(--sidebar-foreground))]"
            aria-label="Expand sidebar"
          >
            <ChevronLeft className="h-4 w-4 rotate-180" />
          </Button>
        )}
        <NavLink
          to="/settings"
          title={!sidebarOpen ? "Settings" : undefined}
          className={({ isActive }) =>
            cn(
              'group flex items-center gap-3 rounded-lg text-sm font-medium transition-all duration-200',
              sidebarOpen ? 'px-3 py-2.5' : 'px-3 py-3 justify-center',
              isActive
                ? 'bg-[hsl(var(--sidebar-foreground))]/10 text-[hsl(var(--sidebar-foreground))]'
                : 'text-[hsl(var(--sidebar-foreground))]/60 hover:bg-[hsl(var(--sidebar-foreground))]/8 hover:text-[hsl(var(--sidebar-foreground))]'
            )
          }
        >
          <Settings className="h-5 w-5 flex-shrink-0 transition-transform group-hover:rotate-90 duration-300" />
          {sidebarOpen && <span>Settings</span>}
        </NavLink>
        <Button
          variant="ghost"
          title={!sidebarOpen ? "Logout" : undefined}
          className={cn(
            "w-full gap-3 text-[hsl(var(--sidebar-foreground))]/60 hover:text-destructive hover:bg-destructive/10 rounded-lg",
            sidebarOpen ? "justify-start px-3" : "justify-center"
          )}
          onClick={logout}
        >
          <LogOut className="h-5 w-5 flex-shrink-0" />
          {sidebarOpen && <span>Logout</span>}
        </Button>
      </div>
    </div>
  )
}
