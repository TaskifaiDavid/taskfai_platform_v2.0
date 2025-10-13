import { useState } from 'react'
import { useLogin } from '@/api/auth'
import { mfaApi } from '@/api/mfa'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useUIStore } from '@/stores/ui'
import { Loader2, Shield } from 'lucide-react'
import { useAuthStore } from '@/stores/auth'
import { useNavigate } from 'react-router-dom'

interface LoginFormProps {
  initialEmail?: string
}

type LoginStep = 'credentials' | 'mfa'

export function LoginForm({ initialEmail }: LoginFormProps) {
  const [step, setStep] = useState<LoginStep>('credentials')
  const [email, setEmail] = useState(initialEmail || '')
  const [password, setPassword] = useState('')
  const [mfaCode, setMfaCode] = useState('')
  const [tempToken, setTempToken] = useState<string | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)

  const login = useLogin()
  const addNotification = useUIStore((state) => state.addNotification)
  const setToken = useAuthStore((state) => state.setToken)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (step === 'credentials') {
      try {
        // Step 1: Initial login with email/password
        const response = await login.mutateAsync({ email, password })

        // Check if MFA is required
        if ((response as any).requires_mfa) {
          setTempToken((response as any).temp_token)
          setStep('mfa')
          addNotification({
            type: 'info',
            title: '2FA Required',
            message: 'Enter your 6-digit authentication code',
          })
        } else {
          // Standard login success (no MFA)
          addNotification({
            type: 'success',
            title: 'Welcome back!',
            message: 'You have successfully logged in',
          })
        }
      } catch (error: any) {
        addNotification({
          type: 'error',
          title: 'Login failed',
          message: error?.response?.data?.detail || 'Invalid email or password',
        })
      }
    } else if (step === 'mfa') {
      // Step 2: Verify MFA code
      try {
        setIsVerifying(true)
        const response = await mfaApi.verifyLoginMFA(tempToken!, mfaCode)

        // Store token and redirect
        if (response.access_token) {
          setToken(response.access_token)
          addNotification({
            type: 'success',
            title: 'Welcome back!',
            message: 'Authentication successful',
          })
          navigate('/dashboard')
        }
      } catch (error: any) {
        addNotification({
          type: 'error',
          title: 'Invalid Code',
          message: error?.response?.data?.detail || 'The authentication code is incorrect',
        })
      } finally {
        setIsVerifying(false)
      }
    }
  }

  return (
    <div className="w-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          {step === 'credentials' ? 'Login' : 'Two-Factor Authentication'}
        </h2>
        <p className="text-sm text-muted-foreground">
          {step === 'credentials'
            ? 'Sign in to your account'
            : 'Enter the 6-digit code from your authenticator app'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {step === 'credentials' ? (
          <>
            {/* Email & Password Fields */}
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
          </>
        ) : (
          <>
            {/* MFA Code Field */}
            <div className="space-y-2">
              <Label htmlFor="mfa-code" className="text-sm font-medium text-foreground flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Authentication Code
              </Label>
              <Input
                id="mfa-code"
                type="text"
                maxLength={6}
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
                placeholder="000000"
                className="h-11 text-center text-2xl tracking-widest font-mono border-border bg-background focus:border-primary focus:ring-primary"
                required
                autoFocus
              />
              <p className="text-xs text-muted-foreground">
                Open your authenticator app to get your code
              </p>
            </div>

            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setStep('credentials')
                  setMfaCode('')
                  setTempToken(null)
                }}
                className="flex-1"
                disabled={isVerifying}
              >
                Back
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-primary hover:bg-primary/90 text-white font-medium"
                disabled={isVerifying || mfaCode.length !== 6}
              >
                {isVerifying ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  'Verify'
                )}
              </Button>
            </div>
          </>
        )}
      </form>
    </div>
  )
}
