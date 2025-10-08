import { Card, CardContent } from '@/components/ui/card'
import { Shield } from 'lucide-react'

export function Admin() {
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

      <Card className="border-border bg-card shadow-sm">
        <CardContent className="flex flex-col items-center justify-center p-16">
          <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-destructive/20 to-destructive/10 flex items-center justify-center border border-destructive/30 shadow-lg mb-6">
            <Shield className="h-10 w-10 text-destructive" />
          </div>
          <p className="text-xl font-semibold text-foreground mb-2">Admin Features Coming Soon</p>
          <p className="text-sm text-muted-foreground text-center max-w-md">
            Tenant management, user administration, and platform monitoring features will be available here
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
