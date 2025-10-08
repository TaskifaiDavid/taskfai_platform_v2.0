import { useAuthStore } from '@/stores/auth'
import { useNavigate } from 'react-router-dom'
import { useUIStore } from '@/stores/ui'

export function useAuth() {
  const { user, token, isAuthenticated, setAuth, clearAuth } = useAuthStore()
  const navigate = useNavigate()
  const addNotification = useUIStore((state) => state.addNotification)

  const login = (user: typeof useAuthStore.getState.arguments[0], token: string) => {
    setAuth(user as never, token)
    navigate('/dashboard')
    addNotification({
      type: 'success',
      title: 'Welcome back!',
      message: `Logged in as ${user.email}`,
    })
  }

  const logout = () => {
    clearAuth()
    navigate('/login')
    addNotification({
      type: 'info',
      title: 'Logged out',
      message: 'You have been logged out successfully',
    })
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
  }
}
