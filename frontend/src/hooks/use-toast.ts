/**
 * Toast Hook Wrapper
 *
 * Wraps react-hot-toast to match shadcn/ui toast API pattern
 */

import toast from 'react-hot-toast'

export interface ToastProps {
  title?: string
  description?: string
  variant?: 'default' | 'destructive'
  duration?: number
}

export function useToast() {
  return {
    toast: ({ title, description, variant = 'default', duration = 4000 }: ToastProps) => {
      const message = title && description
        ? `${title}\n${description}`
        : title || description || ''

      if (variant === 'destructive') {
        toast.error(message, {
          duration,
          style: {
            background: 'hsl(var(--destructive))',
            color: 'hsl(var(--destructive-foreground))',
          },
        })
      } else {
        toast.success(message, {
          duration,
          style: {
            background: 'hsl(var(--background))',
            color: 'hsl(var(--foreground))',
            border: '1px solid hsl(var(--border))',
          },
        })
      }
    }
  }
}
