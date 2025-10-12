import { useState } from 'react'
import { useLogin } from '@/api/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useUIStore } from '@/stores/ui'
import { Loader2 } from 'lucide-react'

interface LoginFormProps {
  initialEmail?: string
}

export function LoginForm({ initialEmail }: LoginFormProps) {
  const [email, setEmail] = useState(initialEmail || '')
  const [password, setPassword] = useState('')

  const login = useLogin()
  const addNotification = useUIStore((state) => state.addNotification)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      // Direct subdomain login: Standard auth flow
      await login.mutateAsync({ email, password })
      addNotification({
        type: 'success',
        title: 'Welcome back!',
        message: 'You have successfully logged in',
      })
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: 'Login failed',
        message: error?.response?.data?.detail || 'Invalid email or password',
      })
    }
  }

  return (
    <div className="w-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-foreground mb-2">Login</h2>
        <p className="text-sm text-muted-foreground">Sign in to your account</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="email" className="text-sm font-medium text-foreground">
            Email
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="yourname@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={login.isPending}
            className="h-11 border-border bg-background focus:border-primary focus:ring-primary"
            autoFocus
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password" className="text-sm font-medium text-foreground">
            Password
          </Label>
          <Input
            id="password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={login.isPending}
            className="h-11 border-border bg-background focus:border-primary focus:ring-primary"
          />
        </div>

        <Button
          type="submit"
          className="w-full h-11 bg-primary hover:bg-primary/90 text-white font-medium shadow-lg hover:shadow-xl transition-all"
          disabled={login.isPending}
        >
          {login.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Signing in...
            </>
          ) : (
            'Sign In'
          )}
        </Button>
      </form>
    </div>
  )
}
