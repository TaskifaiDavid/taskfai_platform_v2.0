import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Shield, Building2, Users, BarChart3 } from 'lucide-react'

export function Admin() {
  const navigate = useNavigate()

  return (
    <div className="space-y-8 animate-in fade-in-0 duration-500">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-destructive/20 to-destructive/10 flex items-center justify-center border border-destructive/30 shadow-sm">
          <Shield className="h-6 w-6 text-destructive" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Platform administration and tenant management</p>
        </div>
      </div>

      {/* Admin Features Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Tenant Management */}
        <Card className="border-border bg-card shadow-sm hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/admin/tenants')}>
          <CardHeader>
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center border border-primary/30 shadow-sm mb-4">
              <Building2 className="h-6 w-6 text-primary" />
            </div>
            <CardTitle>Tenant Management</CardTitle>
            <CardDescription>
              View and manage all customer organizations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full">
              Manage Tenants
            </Button>
          </CardContent>
        </Card>

        {/* User Management */}
        <Card className="border-border bg-card shadow-sm opacity-60">
          <CardHeader>
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-500/10 flex items-center justify-center border border-blue-500/30 shadow-sm mb-4">
              <Users className="h-6 w-6 text-blue-500" />
            </div>
            <CardTitle>User Management</CardTitle>
            <CardDescription>
              Manage users and access control
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full" disabled>
              Coming Soon
            </Button>
          </CardContent>
        </Card>

        {/* Platform Analytics */}
        <Card className="border-border bg-card shadow-sm opacity-60">
          <CardHeader>
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-500/10 flex items-center justify-center border border-purple-500/30 shadow-sm mb-4">
              <BarChart3 className="h-6 w-6 text-purple-500" />
            </div>
            <CardTitle>Platform Analytics</CardTitle>
            <CardDescription>
              Monitor platform usage and performance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full" disabled>
              Coming Soon
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
