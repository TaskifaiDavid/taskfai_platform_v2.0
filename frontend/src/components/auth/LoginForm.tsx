import { useState } from 'react'
import { useLogin } from '@/api/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useUIStore } from '@/stores/ui'
import { Loader2, Github } from 'lucide-react'

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
      await login.mutateAsync({ email, password })
      addNotification({
        type: 'success',
        title: 'Welcome back!',
        message: 'You have successfully logged in',
      })
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Login failed',
        message: 'Invalid email or password',
      })
    }
  }

  return (
    <div className="w-full">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-foreground mb-2">Sign Up</h2>
        <p className="text-sm text-muted-foreground">Get started with TaskifAI today</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="email" className="text-sm font-semibold text-foreground">
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
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password" className="text-sm font-semibold text-foreground">
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

        {/* Terms Text */}
        <p className="text-xs text-center text-muted-foreground">
          By clicking any of the Sign Up buttons, I agree to the{' '}
          <a href="#" className="text-primary hover:underline font-medium">
            terms of service
          </a>
        </p>

        <Button
          type="submit"
          className="w-full h-12 bg-primary hover:bg-primary/90 text-white font-semibold text-sm uppercase tracking-wide shadow-lg hover:shadow-xl transition-all"
          disabled={login.isPending}
        >
          {login.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Signing in...
            </>
          ) : (
            'SIGN UP'
          )}
        </Button>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-card text-muted-foreground font-medium">or</span>
          </div>
        </div>

        {/* OAuth Buttons */}
        <div className="space-y-3">
          <Button
            type="button"
            variant="outline"
            className="w-full h-12 border-border hover:bg-background/50 hover:border-primary/50 text-foreground font-medium transition-all"
            onClick={() => addNotification({
              type: 'info',
              title: 'Coming Soon',
              message: 'OAuth authentication will be available soon',
            })}
          >
            <Github className="mr-3 h-5 w-5" />
            SIGN UP WITH GITHUB
          </Button>

          <Button
            type="button"
            variant="outline"
            className="w-full h-12 border-border hover:bg-background/50 hover:border-primary/50 text-foreground font-medium transition-all"
            onClick={() => addNotification({
              type: 'info',
              title: 'Coming Soon',
              message: 'OAuth authentication will be available soon',
            })}
          >
            <svg className="mr-3 h-5 w-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            SIGN UP WITH GOOGLE
          </Button>

          <Button
            type="button"
            variant="outline"
            className="w-full h-12 border-border hover:bg-background/50 hover:border-primary/50 text-foreground font-medium transition-all"
            onClick={() => addNotification({
              type: 'info',
              title: 'Coming Soon',
              message: 'OAuth authentication will be available soon',
            })}
          >
            <svg className="mr-3 h-5 w-5" viewBox="0 0 23 23">
              <path fill="#f3f3f3" d="M0 0h23v23H0z"/>
              <path fill="#f35325" d="M1 1h10v10H1z"/>
              <path fill="#81bc06" d="M12 1h10v10H12z"/>
              <path fill="#05a6f0" d="M1 12h10v10H1z"/>
              <path fill="#ffba08" d="M12 12h10v10H12z"/>
            </svg>
            SIGN UP WITH MICROSOFT
          </Button>
        </div>

        {/* Demo Credentials */}
        <div className="pt-4 mt-4 border-t border-border">
          <p className="text-xs text-center text-muted-foreground">
            Demo: <span className="font-mono text-foreground font-semibold">admin@demo.com</span> / <span className="font-mono text-foreground font-semibold">password</span>
          </p>
        </div>
      </form>
    </div>
  )
}
