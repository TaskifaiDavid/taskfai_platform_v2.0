import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'
import { Loader2, AlertCircle } from 'lucide-react'
import { jwtDecode } from 'jwt-decode'

/**
 * Auth Callback Handler
 *
 * Handles the redirect from central login portal (app.taskifai.com) after
 * successful tenant discovery. Extracts token from URL, stores it, and
 * redirects to dashboard.
 *
 * URL Format: https://tenant.taskifai.com/auth/callback?token=xxx
 */
export function AuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const processAuthCallback = async () => {
      try {
        // Extract token from URL
        const token = searchParams.get('token')

        if (!token) {
          setError('No authentication token provided')
          // Redirect to login after 2 seconds
          setTimeout(() => navigate('/login'), 2000)
          return
        }

        // Decode token to extract user info
        let userInfo: any
        try {
          userInfo = jwtDecode(token)
        } catch (decodeError) {
          setError('Invalid authentication token')
          setTimeout(() => navigate('/login'), 2000)
          return
        }

        // Validate token has required claims
        if (!userInfo.sub || !userInfo.email || !userInfo.tenant_id || !userInfo.subdomain) {
          setError('Token missing required information')
          setTimeout(() => navigate('/login'), 2000)
          return
        }

        // Store token and user info in auth store
        const user = {
          user_id: userInfo.sub,
          email: userInfo.email,
          role: userInfo.role || 'analyst',
          full_name: userInfo.full_name || userInfo.email.split('@')[0],
          created_at: new Date().toISOString()
        }

        setAuth(user, token)

        // Small delay to show "Completing login..." message
        await new Promise(resolve => setTimeout(resolve, 500))

        // Redirect to dashboard
        navigate('/dashboard', { replace: true })

      } catch (err) {
        console.error('Auth callback error:', err)
        setError('Authentication failed. Please try again.')
        setTimeout(() => navigate('/login'), 2000)
      }
    }

    processAuthCallback()
  }, [searchParams, navigate, setAuth])

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
          <h2 className="text-2xl font-bold text-foreground">Authentication Error</h2>
          <p className="text-muted-foreground max-w-md">{error}</p>
          <p className="text-sm text-muted-foreground">Redirecting to login...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
        <h2 className="text-2xl font-bold text-foreground">Completing Login</h2>
        <p className="text-muted-foreground">Setting up your workspace...</p>
      </div>
    </div>
  )
}
