import { useSearchParams } from 'react-router-dom'
import { LoginForm } from '@/components/auth/LoginForm'
import { TenantBadge } from '@/components/layout/TenantBadge'
import { Check, Sparkles } from 'lucide-react'

export function Login() {
  const [searchParams] = useSearchParams()
  const emailParam = searchParams.get('email')
  return (
    <div className="flex min-h-screen">
      {/* Left Side - Marketing Content */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-background via-background to-primary/5 p-12 flex-col justify-between border-r border-border">
        <div>
          {/* Logo */}
          <div className="mb-12 flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center border border-primary/30 shadow-sm">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <h1 className="text-3xl font-bold text-foreground">TaskifAI</h1>
          </div>

          {/* Hero Content */}
          <div className="max-w-lg">
            <h2 className="text-4xl font-bold text-foreground leading-tight mb-4">
              Try the world's #1 sales analytics platform for free!
            </h2>
            <p className="text-lg text-muted-foreground mb-8">
              Let TaskifAI handle the complexities of sales data analysis so you can focus on growing your business!
            </p>

            {/* Features List */}
            <div className="space-y-4 mb-12">
              <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                Start for free and save time with TaskifAI!
              </p>

              <div className="space-y-4">
                <div className="flex items-start gap-3 group">
                  <div className="h-6 w-6 rounded-lg bg-success/10 flex items-center justify-center flex-shrink-0 group-hover:bg-success/20 transition-colors">
                    <Check className="h-4 w-4 text-success" />
                  </div>
                  <span className="text-foreground font-medium">Unlimited vendor integrations & real-time sync</span>
                </div>
                <div className="flex items-start gap-3 group">
                  <div className="h-6 w-6 rounded-lg bg-success/10 flex items-center justify-center flex-shrink-0 group-hover:bg-success/20 transition-colors">
                    <Check className="h-4 w-4 text-success" />
                  </div>
                  <span className="text-foreground font-medium">AI-powered insights & automated reporting</span>
                </div>
                <div className="flex items-start gap-3 group">
                  <div className="h-6 w-6 rounded-lg bg-success/10 flex items-center justify-center flex-shrink-0 group-hover:bg-success/20 transition-colors">
                    <Check className="h-4 w-4 text-success" />
                  </div>
                  <span className="text-foreground font-medium">Multi-tenant architecture for resellers</span>
                </div>
                <div className="flex items-start gap-3 group">
                  <div className="h-6 w-6 rounded-lg bg-success/10 flex items-center justify-center flex-shrink-0 group-hover:bg-success/20 transition-colors">
                    <Check className="h-4 w-4 text-success" />
                  </div>
                  <span className="text-foreground font-medium">Advanced analytics & customizable dashboards</span>
                </div>
              </div>
            </div>

            {/* Trust Section */}
            <div className="pt-8 border-t border-border">
              <p className="text-sm font-semibold text-foreground mb-2">
                Built for businesses
              </p>
              <p className="text-sm text-muted-foreground">
                Trusted by sales teams worldwide
              </p>
            </div>
          </div>
        </div>

        {/* Bottom - Tenant Badge */}
        <div className="flex justify-start">
          <TenantBadge />
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-card">
        <div className="w-full max-w-md">
          <LoginForm initialEmail={emailParam || undefined} />
        </div>
      </div>
    </div>
  )
}
