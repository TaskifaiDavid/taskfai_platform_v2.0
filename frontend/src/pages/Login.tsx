import { useSearchParams } from 'react-router-dom'
import { LoginForm } from '@/components/auth/LoginForm'
import { TenantBadge } from '@/components/layout/TenantBadge'
import { Sparkles } from 'lucide-react'

export function Login() {
  const [searchParams] = useSearchParams()
  const emailParam = searchParams.get('email')

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 p-4">
      {/* Centered Login Card */}
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center gap-4">
          <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center border border-primary/30 shadow-lg">
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-3xl font-bold text-foreground">TaskifAI</h1>
        </div>

        {/* Login Form Card */}
        <div className="bg-card border border-border rounded-2xl shadow-2xl p-8">
          <LoginForm initialEmail={emailParam || undefined} />
        </div>

        {/* Tenant Badge - Bottom Center */}
        <div className="mt-8 flex justify-center">
          <TenantBadge />
        </div>
      </div>
    </div>
  )
}
