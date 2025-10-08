import { create } from 'zustand'
import toast from 'react-hot-toast'

interface Notification {
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
}

interface UIState {
  sidebarOpen: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  addNotification: (notification: Notification) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  addNotification: (notification) => {
    const message = notification.message
      ? `${notification.title}: ${notification.message}`
      : notification.title

    switch (notification.type) {
      case 'success':
        toast.success(message)
        break
      case 'error':
        toast.error(message)
        break
      case 'warning':
        toast(message, { icon: '⚠️' })
        break
      case 'info':
        toast(message, { icon: 'ℹ️' })
        break
    }
  },
}))
